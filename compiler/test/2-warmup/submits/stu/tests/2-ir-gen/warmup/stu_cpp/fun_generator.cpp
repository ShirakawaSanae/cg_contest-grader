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

    // callee 函数
    std::vector<Type *> Ints(1, Int32Type);
    auto *calleeFun = Function::create(FunctionType::get(Int32Type, Ints), "callee", module);
    auto *bb0 = BasicBlock::create(module, "callee", calleeFun);
    builder->set_insert_point(bb0);

    std::vector<Value *> args;
    for (auto &arg: calleeFun->get_args()) {
        args.push_back(&arg);
    }
    auto *aAlloca = builder->create_alloca(Int32Type);
    builder->create_store(args[0], aAlloca);
    auto *a = builder->create_load(aAlloca);
    auto *mul = builder->create_imul(CONST_INT(2), a);
    builder->create_ret(mul);

    // main 函数
    auto *mainFun = Function::create(FunctionType::get(Int32Type, {}),
                                    "main", module);
    // 创建基本块
    auto *bb1 = BasicBlock::create(module, "main", mainFun);
    builder->set_insert_point(bb1);
    auto *call = builder->create_call(calleeFun, {CONST_INT(110)});
    builder->create_ret(call);

    std::cout << module->print();
    delete module;
    return 0;
}
