#ifndef __POWER_H__
#define __POWER_H__

#include <string>

using namespace std;

class Power {
    public:
        string type;
        double percent;

        Power(string powerType="electric", double percentFull=100) {
            type = powerType;
            percent = percentFull;
        }
};

#endif // __ENERGY_H__