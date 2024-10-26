from flask import jsonify

class Result():
    def __init__(self, status="success", data={}, message="", code=200, meta={}):
        self.status = status
        self.data = data
        self.message = message
        self.code = code
        self.meta = meta
    
    def __repr__(self):
        if self.status == '':
            status_display = "''"
        else:
            status_display = self.status
        
        if self.message == '':
            message_display = "''"
        else:
            message_display = self.message
        
        return f"{{{self.classname} status: {status_display}, data: {self.data}, message: {message_display}, code: {self.code}, meta: {self.meta}}}"
    
    def to_json(self):
        return jsonify({
            "status": self.status,
            "data": self.data,
            "message": self.message,
            "code": self.code,
            "meta": self.meta
        })
    
    def to_api_response(self):
        return (self.to_json(), self.code)