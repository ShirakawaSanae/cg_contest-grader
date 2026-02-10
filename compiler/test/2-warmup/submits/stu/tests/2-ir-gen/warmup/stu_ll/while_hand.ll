; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 {
    0:
    ; %1 points to a
    %1 = alloca i32
    ; %2 points to i
    %2 = alloca i32
    store i32 10, i32* %1
    store i32 0, i32* %2
    %3 = load i32, i32* %2
    %4 = icmp slt i32 %3, 10
    br i1 %4, label %LOOP, label %ENDLOOP

LOOP:
    %5 = load i32, i32* %2
    %6 = add i32 %5, 1
    store i32 %6, i32* %2
    %7 = load i32, i32* %1
    %8 = add i32 %7, %6
    store i32 %8, i32* %1
    %9 = icmp slt i32 %6, 10
    br i1 %9, label %LOOP, label %ENDLOOP

ENDLOOP:
    %10 = load i32, i32* %1
    ret i32 %10
}
