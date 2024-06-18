#ifndef __RESULT_H__
#define __RESULT_H__

#include <string>
#include <unordered_map>

using namespace std;

class Result {
    public:
        string status;
        unordered_map<string, string> data;
        string message;
        int code;
        unordered_map<string, string> meta;

        Result(string statusVal="success", unordered_map<string, string> dataVal=unordered_map<string, string>(), string messageVal="", int codeVal=200, unordered_map<string, string> metaVal=unordered_map<string, string>()) {
            status = statusVal;
            data = dataVal;
            message = messageVal;
            code = codeVal;
            meta = metaVal;
        }
};

#endif // __RESULT_H__