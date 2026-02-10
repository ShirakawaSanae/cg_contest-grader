#include <iostream>
using namespace std;
int main()
{
    int x = 0;
    int y = 0;
    while (cin >> x >> y) {
        while (x != y) {
            if (x > y) {
                x -= y;
            }
            else if(x < y) {
                y -= x;
            }
        }
        cout << x << endl;
    }
    return 0;
}

