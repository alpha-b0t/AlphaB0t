#ifndef __CAR_H__
#define __CAR_H__

#include <string>
using namespace std;
class Car {
    public:
        string make;
        string model;

        Car(string makerName, string modelName) {
            make = makerName;
            model = modelName;
        }
};

class EV : public Car {
    public:
        double batteryLevel;

        EV(string makerName, string modelName, double batteryPercentage) : Car(makerName, modelName) {
            batteryLevel = batteryPercentage;
        }
};

#endif // __CAR_H__