import math
import torch
import torch_npu
import triton
import triton.language as tl
import time

DEVICE = torch.device("npu" if torch.npu.is_available() else "cpu")

@triton.jit
def _paged_attention_kernel(
	q_ptr,
	k_ptr,
	v_ptr,
	block_table_ptr,
	context_lens_ptr,
	out_ptr,
	stride_qz, stride_qh, stride_qd,
	stride_kb, stride_kh, stride_kd, stride_kbo,
	stride_vb, stride_vh, stride_vd, stride_vbo,
	stride_bt,
	stride_oz, stride_oh, stride_od,
	head_size,
	BLOCK_D: tl.constexpr,
	BLOCK_M: tl.constexpr,
	MAX_BLOCKS: tl.constexpr,
):
	# 你可以传入更多的 tl.constexper
    # TODO:
    # 请实现 triton kernel


def paged_attention_triton(
	query: torch.Tensor,        # [num_tokens, num_heads, head_size]
	key_cache: torch.Tensor,    # [num_blocks, num_heads, head_size, block_size]
	value_cache: torch.Tensor,  # [num_blocks, num_heads, head_size, block_size]
	block_tables: torch.Tensor, # [num_tokens, max_num_blocks] mapping block index per token
	context_lens: torch.Tensor, # [num_tokens] effective length (<= max_num_blocks * block_size)
) -> torch.Tensor:
	num_blocks, num_heads, head_size, block_size = key_cache.shape
	num_tokens = query.shape[0]
	assert value_cache.shape == key_cache.shape
	assert block_tables.shape[0] == num_tokens
	assert context_lens.shape[0] == num_tokens

	block_d = 1 << (head_size - 1).bit_length()
	if block_d > 128:
		raise ValueError(f"head_size={head_size} is too large for this kernel")

	query = query.contiguous()
	key_cache = key_cache.contiguous()
	value_cache = value_cache.contiguous()
	block_tables = block_tables.contiguous()
	context_lens = context_lens.contiguous()

	out = torch.empty_like(query, dtype=torch.float32)
	# 调用 triton kernel 计算 out
	# TODO: 

	return out.to(query.dtype)

def paged_attention_ref(
	query: torch.Tensor,        # [num_tokens, num_heads, head_size]
	key_cache: torch.Tensor,    # [num_blocks, num_heads, head_size, block_size]
	value_cache: torch.Tensor,  # [num_blocks, num_heads, head_size, block_size]
	block_tables: torch.Tensor, # [num_tokens, max_num_blocks] mapping block index per token
	context_lens: torch.Tensor, # [num_tokens] effective length (<= max_num_blocks * block_size)
) -> torch.Tensor:
	"""Reference paged attention on CPU.

	Shapes
	- query: [num_tokens, num_heads, head_size]
	- key_cache/value_cache: [num_blocks, num_heads, head_size, block_size]
	- block_tables: [num_tokens, max_num_blocks] mapping block index per token
	- context_lens: [num_tokens] effective length (<= max_num_blocks * block_size)
	"""

	num_tokens, num_heads, head_size = query.shape
	block_size = key_cache.shape[3]
	out = torch.empty_like(query, dtype=torch.float32)
	scale = (1.0 / head_size**0.5)

	for t in range(num_tokens):
		ctx = int(context_lens[t])
		if ctx == 0:
			out[t].zero_()
			continue

		# Gather keys/values for this token across blocks.
		keys = []
		vals = []
		for j in range(ctx):
			blk = int(block_tables[t, j // block_size])
			off = j % block_size
			k = key_cache[blk, :, :, off]
			v = value_cache[blk, :, :, off]
			keys.append(k)
			vals.append(v)

		k_stacked = torch.stack(keys, dim=0)  # [ctx, num_heads, head_size]
		v_stacked = torch.stack(vals, dim=0)  # [ctx, num_heads, head_size]

		# Compute attention for a single query token against its context.
		q = query[t]  # [num_heads, head_size]
		logits = (q.unsqueeze(0) * k_stacked).sum(-1) * scale  # [ctx, num_heads]
		attn = torch.softmax(logits, dim=0)  # softmax over ctx
		weighted = (attn.unsqueeze(-1) * v_stacked).sum(0)  # [num_heads, head_size]
		out[t].copy_(weighted)

	return out.to(query.dtype)


def make_random_inputs(
	num_tokens: int = 4,
	num_heads: int = 2,
	head_size: int = 64,
	block_size: int = 16,
	max_ctx: int = 48,
	device: torch.device | None = None,
	dtype: torch.dtype = torch.float32,
):

	device = device or DEVICE
	max_blocks = (max_ctx + block_size - 1) // block_size
	num_blocks = max_blocks + 1

	query = torch.randn(num_tokens, num_heads, head_size, device=device, dtype=dtype).contiguous()
	key_cache = torch.randn(num_blocks, num_heads, head_size, block_size, device=device, dtype=dtype).contiguous()
	value_cache = torch.randn(num_blocks, num_heads, head_size, block_size, device=device, dtype=dtype).contiguous()

	context_lens = torch.randint(1, max_ctx + 1, (num_tokens,), device=device, dtype=torch.int32).contiguous()
	block_tables = torch.zeros((num_tokens, max_blocks), device=device, dtype=torch.int32)
	for i in range(num_tokens):
		block_tables[i] = torch.arange(max_blocks, device=device, dtype=torch.int32)
	block_tables = block_tables.contiguous()

	return query, key_cache, value_cache, block_tables, context_lens


def demo_cpu():
	torch.manual_seed(42)
	query, key_cache, value_cache, block_tables, context_lens = make_random_inputs()
	out = paged_attention_ref(query, key_cache, value_cache, block_tables, context_lens)
	print("CPU paged attention output mean:", float(out.mean()))


def demo_compare():
	if not torch.npu.is_available():
		print("NPU not available, skipping Triton demo")
		return

	torch.manual_seed(42)
	query, key_cache, value_cache, block_tables, context_lens = make_random_inputs(dtype=torch.float16, device=DEVICE)
	ref = paged_attention_ref(query, key_cache, value_cache, block_tables, context_lens)
	out = paged_attention_triton(query, key_cache, value_cache, block_tables, context_lens)
	torch.testing.assert_close(out, ref, rtol=1e-2, atol=1e-2)
	max_diff = (out - ref).abs().max().item()
	print("Triton vs ref max diff:", max_diff)
	with open("1.out", "w") as f:
		f.write(f"{max_diff}")

def demo_bench(num_warmup: int = 10, num_iters: int = 50):
	if not torch.npu.is_available():
		print("NPU not available, skipping Triton benchmark")
		return

	torch.manual_seed(0)
	query, key_cache, value_cache, block_tables, context_lens = make_random_inputs(
		num_tokens=32,
		num_heads=8,
		head_size=64,
		block_size=16,
		max_ctx=128,
		dtype=torch.float16,
		device=DEVICE,
	)

	def run_triton():
		_ = paged_attention_triton(query, key_cache, value_cache, block_tables, context_lens)

	def run_torch():
		_ = paged_attention_ref(query, key_cache, value_cache, block_tables, context_lens)

	# Warmup
	for _ in range(num_warmup):
		run_triton()
		torch.npu.synchronize()

	try:
		from triton.testing import do_bench

		triton_ms = do_bench(run_triton, warmup=num_warmup, rep=num_iters)
		torch_ms = do_bench(run_torch, warmup=num_warmup, rep=num_iters)
	except Exception:
		# Fallback timing
		def time_ms(fn):
			start = time.time()
			for _ in range(num_iters):
				fn()
			torch.npu.synchronize()
			return (time.time() - start) * 1000.0 / num_iters

		triton_ms = time_ms(run_triton)
		torch_ms = time_ms(run_torch)

	print(f"Triton avg ms: {triton_ms:.3f}")
	print(f"Torch ref avg ms: {torch_ms:.3f}")
	print(f"Acceleration ratio: {torch_ms / triton_ms:.2f}x")
	print(f"{torch_ms/triton_ms:.2f}")


if __name__ == "__main__":
	# demo_cpu()
	# Uncomment to run on NPU
	demo_compare()
	#demo_bench()
