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
    Type *FloatType = module->get_float_type();
    // main 函数
    auto *mainFun = Function::create(FunctionType::get(Int32Type, {}),
                                    "main", module);
    // 创建基本块
    auto *bb = BasicBlock::create(module, "main", mainFun);
    builder->set_insert_point(bb);

    auto *aAlloca = builder->create_alloca(FloatType);
    builder->create_store(CONST_FP(5.555), aAlloca);

    auto *trueBB = BasicBlock::create(module, "trueBB", mainFun);
    auto *falseBB = BasicBlock::create(module, "falseBB", mainFun);
    auto *retBB = BasicBlock::create(module, "retBB", mainFun);
    auto *retAlloca = builder->create_alloca(Int32Type);

    auto *a = builder->create_load(aAlloca);
    auto *fcmp = builder->create_fcmp_gt(a, CONST_FP(1));
    builder->create_cond_br(fcmp, trueBB, falseBB);

    // trueBB 块
    builder->set_insert_point(trueBB);
    builder->create_store(CONST_INT(233), retAlloca);
    builder->create_br(retBB);

    // falseBB 块
    builder->set_insert_point(falseBB);
    builder->create_store(CONST_INT(0), retAlloca);
    builder->create_br(retBB);

    // retBB 块
    builder->set_insert_point(retBB);
    auto *ret = builder->create_load(retAlloca);
    builder->create_ret(ret);

    std::cout << module->print();
    delete module;
    return 0;
}
