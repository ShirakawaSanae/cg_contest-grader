#include "LICM.hpp"

#include <memory>
#include <vector>

#include "BasicBlock.hpp"
#include "Function.hpp"
#include "Instruction.hpp"
#include "PassManager.hpp"

/**
 * @brief 循环不变式外提Pass的主入口函数
 * 
 */
void LoopInvariantCodeMotion::run()
{
    func_info_ = new FuncInfo(m_);
    func_info_->run();
    for (auto func : m_->get_functions())
    {
        if (func->is_declaration()) continue;
        loop_detection_ = new LoopDetection(func);
        loop_detection_->run();
        for (auto loop : loop_detection_->get_loops())
        {
            // 遍历处理顶层循环
            if (loop->get_parent() == nullptr) traverse_loop(loop);
        }
        delete loop_detection_;
        loop_detection_ = nullptr;
    }
    delete func_info_;
    func_info_ = nullptr;
}

/**
 * @brief 遍历循环及其子循环
 * @param loop 当前要处理的循环
 * 
 */
void LoopInvariantCodeMotion::traverse_loop(Loop* loop)
{
    // 先外层再内层，这样不用在插入 preheader 后更改循环
    run_on_loop(loop);
    for (auto sub_loop : loop->get_sub_loops())
    {
        traverse_loop(sub_loop);
    }
}

std::unordered_set<Value*> LoopInvariantCodeMotion::collect_loop_store_vars(Loop* loop)
{
	// 可能用到
	// FuncInfo::store_ptr, FuncInfo::get_stores
	std::unordered_set<Value*> ret;
	for(auto bb : loop->get_blocks()){
		for(auto inst: bb->get_instructions()){
			if(inst->is_store()){
				auto ptr = FuncInfo::store_ptr(inst->as<StoreInst>());
				ret.emplace(ptr);
			}
			else if(inst->is_call()){
				auto ptrd =  func_info_->get_stores(inst->as<CallInst>());
				for(auto i : ptrd) ret.emplace(i);
			}
		}
	}
	return ret;
}

std::vector<Instruction*> LoopInvariantCodeMotion::collect_insts(Loop* loop)
{
	std::vector<Instruction*> ret;
	for(auto bb : loop->get_blocks()){
		for(auto inst: bb->get_instructions()){
			ret.emplace_back(inst);
		}
	}
	return ret;
}

enum InstructionType: std::uint8_t
{
    UNKNOWN, VARIANT, INVARIANT
};

/**
 * @brief 对单个循环执行不变式外提优化
 * @param loop 要优化的循环
 * 
 */
void LoopInvariantCodeMotion::run_on_loop(Loop* loop)
{
    // 循环 store 过的变量
    std::unordered_set<Value*> loop_stores_var = collect_loop_store_vars(loop);
    // 循环中的所有指令
    std::vector<Instruction*> instructions = collect_insts(loop);
    int insts_count = static_cast<int>(instructions.size());
    // Value* 在 map 内说明它是循环内的指令，InstructionType 指示它是循环变量（每次循环都会变）/ 循环不变量 还是 不知道
    std::unordered_map<Value*, InstructionType> inst_type;
    for (auto i : instructions) inst_type[i] = UNKNOWN;

    // 遍历后是不是还有指令不知道 InstructionType
    bool have_inst_can_not_decide;
    // 是否存在 invariant
    bool have_invariant = false;
    do
    {
        have_inst_can_not_decide = false;
        for (int i = 0; i < insts_count; i++)
        {
            Instruction* inst = instructions[i];
            InstructionType type = inst_type[inst];
            if (type != UNKNOWN) continue;
            // 可能有用的函数
            // FuncInfo::load_ptr, FuncInfo::get_stores, FuncInfo::use_io
if(inst->is_store() || inst->is_ret() || inst->is_br() || inst->is_phi()){
				inst_type[inst] = VARIANT;
				continue;
			}
			if(inst->is_call()){
				auto ca = inst->as<CallInst>();
				auto f = inst->get_operand(0)->as<Function>();
				bool wrong = false;
				if(func_info_->use_io(f)) wrong = true;
				else {
					auto stores = func_info_->get_stores(ca);
					if(!stores.empty()) wrong = true;
					else  {
					auto l = func_info_->get_loads(ca);
					for(auto a : l)
					{
						if(loop_stores_var.count(a)){
							wrong = true;
							break;
						}
					}
				}}
				if(wrong)
				{
					inst_type[inst] = VARIANT;
					continue;
				}
			}
			if(inst->is_load())
			{
				if(loop_stores_var.count(FuncInfo::load_ptr(inst->as<LoadInst>())))
				{
					inst_type[inst] = VARIANT;
					continue;
				}
			}

			bool have_undef = false;
			bool have_var = false;
			for(auto i : inst->get_operands()){
				if(inst_type.count(i)){
					auto get = inst_type[i];
					if(get == UNKNOWN) have_undef = true;
					else if(get == VARIANT){
						inst_type[inst] = VARIANT;
						have_var = true;
						break;
					}
				}
			}
			if(have_var) continue;
			if(have_undef){
				have_inst_can_not_decide = true;
			}
			else {
				inst_type[inst] = INVARIANT;
				have_invariant = true;
			}
        }
    }
    while (have_inst_can_not_decide);

    if (!have_invariant) return;

    auto header = loop->get_header();

    if (header->get_pre_basic_blocks().size() > 1 || header->get_pre_basic_blocks().front()->get_succ_basic_blocks().size() > 1)
    {
        // 插入 preheader
        auto bb = BasicBlock::create(m_, "", loop->get_header()->get_parent());
        loop->set_preheader(bb);

        for (auto phi : loop->get_header()->get_instructions())
        {
            if (phi->get_instr_type() != Instruction::phi) break;
            auto pphi = phi->as<PhiInst>();
			std::map<BasicBlock*, Value*> pres;
			std::map<BasicBlock*, Value*> lats;
			for(auto [ v,b] : pphi->get_phi_pairs())
			{
				if(loop->get_latches().count(b))
				{
					lats.emplace(b, v);
				}
				else pres.emplace(b, v);
			}
			auto nphi = PhiInst::create_phi(pphi->get_type(), bb);
			for(auto [i,j] : pres){
				nphi->add_phi_pair_operand(j, i);
			}
			pphi->remove_all_operands();
			for(auto [i,j] : lats){
				pphi->add_phi_pair_operand(j, i);
			}
			pphi->add_phi_pair_operand(nphi, bb);
        }

        // 可能有用的函数
        // BranchInst::replace_all_bb_match

		auto bbs = header->get_pre_basic_blocks();

		for(auto pre : bbs)
		{
			if(loop->get_latches().count(pre)) continue;
			pre->get_instructions().back()->as<BranchInst>()->replace_all_bb_match(header, bb);
		}

        BranchInst::create_br(header, bb);

        // 若你想维护 LoopDetection 在 LICM 后保持正确
        // auto loop2 = loop->get_parent();
        // while (loop2 != nullptr)
        // {
        //      loop2->add_block(bb);
        //     loop2 = loop2->get_parent();
        // }
    }
    else loop->set_preheader(header->get_pre_basic_blocks().front());

    // insert preheader
    auto preheader = loop->get_preheader();

    auto terminator = preheader->get_instructions().back();
    preheader->get_instructions().pop_back();

    // 可以使用 Function::check_for_block_relation_error 检查基本块间的关系是否正确维护

	for(auto inst : instructions)
	{
		if(inst_type[inst] == INVARIANT)
		{
			auto parent = inst->get_parent();
			parent->remove_instr(inst);
			preheader->add_instruction(inst);
			inst->set_parent(preheader);
		}
	}

    preheader->add_instruction(terminator);

    std::cerr << "licm done\n";
}
