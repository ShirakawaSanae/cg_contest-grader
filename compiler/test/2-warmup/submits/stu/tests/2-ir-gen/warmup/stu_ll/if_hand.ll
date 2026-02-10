; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 {
    0:
    %1 = alloca float
    store float 0x40163851E0000000, float* %1
    %2 = load float, float* %1
    %3 = fcmp ugt float %2, 1.000000e+00
    br i1 %3, label %true, label %false

true:
    ret i32 233

false:
    ret i32 0
}

