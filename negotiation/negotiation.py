from negotiation.concession import calculate_concession


class NegotiationAgent:

    def __init__(self, user_requirements, provider_offer):
        self.user = user_requirements
        self.provider = provider_offer

    def negotiate(self):

        final_offer = {}

        for attribute in self.user:

            user_value = self.user[attribute]
            provider_value = self.provider[attribute]

            final_offer[attribute] = calculate_concession(
                user_value,
                provider_value
            )

        return final_offer
