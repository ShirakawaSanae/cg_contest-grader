#include<stdio.h>

int main()
{
    int x = 0;
    int y = 0;
    while (~scanf("%d%d", &x, &y)) {
        while (x != y) {
            if (x > y) {
                x -= y;
            }
            else if(x < y) {
                y -= x;
            }
        }
        printf("%d\n", x);
    }
    return 0;
}
