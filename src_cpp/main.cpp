#include <iostream>
#include "Result/result.h"

using namespace std;

int main(int argc, char* argv[]) {
    cout << "Running..." << endl;
    
    EV ev("Tesla", "Model Y", 72.3);

    cout << ev.make << " " << ev.model << endl;
    cout << "Battery: " << ev.batteryLevel << "%" << endl;

    Power power;

    cout << power.type << " power at " << power.percent << "%" << endl;

    Result result;

    cout << "result.code: " << result.code << endl;

    cout << "Ending..." << endl;

    return 0;
}