from negotiation.negotiation import NegotiationAgent

user = {
    "price": 200,
    "security": 90,
    "availability": 95
}

provider = {
    "price": 300,
    "security": 80,
    "availability": 92
}

agent = NegotiationAgent(user, provider)

result = agent.negotiate()

print(result)