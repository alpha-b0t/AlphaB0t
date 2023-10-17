class User():
    def __init__(self, user_id, username, email, password):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password = password

        # Dictionary to store user balances on different exchanges
        self.balances = {}

        # List to store user's trading bots
        self.trading_bots = []