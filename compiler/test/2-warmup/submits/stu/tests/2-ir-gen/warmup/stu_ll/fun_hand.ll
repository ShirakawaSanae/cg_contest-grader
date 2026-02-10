; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @callee(i32 %0) #0 {
    %2 = mul i32 2, %0
    ret i32 %2
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 {
    0:
    %1 = call i32 @callee(i32 110)
    ret i32 %1
}
