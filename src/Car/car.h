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
        double speed;
        bool isSelfDriveOn = false;

        EV(string makerName, string modelName, double batteryPercentage) : Car(makerName, modelName) {
            batteryLevel = batteryPercentage;
            speed = 0;
        }

        double charge(float hours, float chargePerHour) {
            batteryLevel += chargePerHour * hours;

            if (batteryLevel > 100) {
                batteryLevel = 100;
            }

            return batteryLevel;
        }

        void turnOnSelfDrive() {
            isSelfDriveOn = true;
        }

        void turnOffSelfDrive() {
            isSelfDriveOn = false;
        }
};

#endif // __CAR_H__
