#include <iostream>
#include "Car/car.h"

using namespace std;

int main(int argc, char* argv[]) {
    cout << "Running..." << endl;
    
    EV car0("Tesla", "Model Y", 72.3);

    cout << car0.make << " " << car0.model << endl;
    cout << "Battery: " << car0.batteryLevel << "%" << endl;

    cout << "Ending..." << endl;

    return 0;
}