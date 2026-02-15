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
	pid_tok = tl.program_id(0)
	pid_head = tl.program_id(1)

	d_offsets = tl.arange(0, BLOCK_D)
	q_mask = d_offsets < head_size
	q = tl.load(
		q_ptr + pid_tok * stride_qz + pid_head * stride_qh + d_offsets * stride_qd,
		mask=q_mask,
		other=0.0,
	).to(tl.float32)

	ctx_len = tl.load(context_lens_ptr + pid_tok).to(tl.int32)	# tokens 的长度
	block_row = block_table_ptr + pid_tok * stride_bt

	head_size_f = tl.full((), head_size, tl.float32)
	scale = tl.rsqrt(head_size_f)
	acc = tl.zeros((BLOCK_D,), dtype=tl.float32)
	row_sum = tl.zeros((), dtype=tl.float32)
	lse = -float("inf")

	num_blocks = (ctx_len + BLOCK_M - 1) // BLOCK_M

	for block_idx in range(num_blocks):
		block_start = block_idx * BLOCK_M
		token_in_blk = tl.arange(0, BLOCK_M).to(tl.int32)  # within-block offsets
		token_offsets = block_start + token_in_blk
		token_mask = token_offsets < ctx_len
		block_number = tl.load(block_row + block_idx).to(tl.int32)

		# [D, M] layout: keep M as contiguous dimension (stride_kbo/stride_vbo == 1)
		kv_mask = (d_offsets[:, None] < head_size) & token_mask[None, :]

		k_block = (
			k_ptr
			+ block_number * stride_kb
			+ pid_head * stride_kh
			+ d_offsets[:, None] * stride_kd
			+ token_in_blk[None, :] * stride_kbo
		)
		k = tl.load(
			k_block,
			mask=kv_mask,
			other=0.0,
		).to(tl.float32)

		logits = tl.sum(k * q[:, None], axis=0) * scale
		logits = tl.where(token_mask, logits, -float("inf"))

		l_i = tl.max(logits, axis=0)
		l_new = tl.maximum(lse, l_i)

		p = tl.exp(logits - l_new) * token_mask

		v_block = (
			v_ptr
			+ block_number * stride_vb
			+ pid_head * stride_vh
			+ d_offsets[:, None] * stride_vd
			+ token_in_blk[None, :] * stride_vbo
		)
		v = tl.load(
			v_block,
			mask=kv_mask,
			other=0.0,
		).to(tl.float32)

		alpha = tl.exp(lse - l_new)
		acc = acc * alpha + tl.sum(v * p[None, :], axis=1)
		row_sum = row_sum * alpha + tl.sum(p, axis=0)
		lse = l_new

	row_sum = tl.maximum(row_sum, 1e-9)
	out = acc / row_sum
	tl.store(
		out_ptr + pid_tok * stride_oz + pid_head * stride_oh + d_offsets * stride_od,
		out,
		mask=q_mask,
	)


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

	grid = (num_tokens, num_heads)
	out = torch.empty_like(query, dtype=torch.float32)

	_paged_attention_kernel[grid](
		query,
		key_cache,
		value_cache,
		block_tables,
		context_lens,
		out,
		query.stride(0), query.stride(1), query.stride(2),
		key_cache.stride(0), key_cache.stride(1), key_cache.stride(2), key_cache.stride(3),
		value_cache.stride(0), value_cache.stride(1), value_cache.stride(2), value_cache.stride(3),
		block_tables.stride(0),
		out.stride(0), out.stride(1), out.stride(2),
		head_size,
		BLOCK_D=block_d,
		BLOCK_M=block_size,
		MAX_BLOCKS=block_tables.shape[1],
	)

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
	demo_cpu()
	# Uncomment to run on NPU
	demo_compare()
	demo_bench()