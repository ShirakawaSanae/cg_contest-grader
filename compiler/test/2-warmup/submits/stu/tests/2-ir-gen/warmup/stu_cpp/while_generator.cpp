#include "BasicBlock.hpp"
#include "Constant.hpp"
#include "Function.hpp"
#include "IRBuilder.hpp"
#include "Module.hpp"
#include "Type.hpp"

#include <iostream>
#include <memory>

#ifdef DEBUG
#define DEBUG_OUTPUT std::cout << __LINE__ << std::endl;  // 输出行号的简单示例
#else
#define DEBUG_OUTPUT
#endif

#define CONST_INT(num) ConstantInt::get(num, module)

#define CONST_FP(num) ConstantFP::get(num, module)  // 得到常数值的表示，方便后面多次用到

int main() {
    auto *module = new Module();
    auto *builder = new IRBuilder(nullptr, module);

    Type *Int32Type = module->get_int32_type();

    // main 函数
    auto *mainFun = Function::create(FunctionType::get(Int32Type, {}),
                                    "main", module);
    // 创建基本块
    auto *bb = BasicBlock::create(module, "main", mainFun);
    builder->set_insert_point(bb);

    auto *aAlloca = builder->create_alloca(Int32Type);
    auto *iAlloca = builder->create_alloca(Int32Type);

    builder->create_store(CONST_INT(10), aAlloca);
    builder->create_store(CONST_INT(0), iAlloca);

    auto *i = builder->create_load(iAlloca);
    auto *icmp = builder->create_icmp_lt(i, CONST_INT(10));

    auto *loopBB = BasicBlock::create(module, "loop", mainFun);
    auto *endBB = BasicBlock::create(module, "end", mainFun);
    builder->create_cond_br(icmp, loopBB, endBB);

    // loop 基本块
    builder->set_insert_point(loopBB);
    i = builder->create_load(iAlloca);
    auto *add = builder->create_iadd(i, CONST_INT(1));
    builder->create_store(add, iAlloca);

    auto *a = builder->create_load(aAlloca);
    add = builder->create_iadd(a, i);
    builder->create_store(add, aAlloca);

    icmp = builder->create_icmp_lt(i, CONST_INT(10));
    builder->create_cond_br(icmp, loopBB, endBB);

    // end 基本块
    builder->set_insert_point(endBB);
    a = builder->create_load(aAlloca);
    builder->create_ret(a);

    std::cout << module->print();
    delete module;
    return 0;
}
