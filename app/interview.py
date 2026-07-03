import json

# QUESTIONS = [
#     "What is your main health problem today?",
#     "Since when are you facing this problem?",
#     "How has the problem changed over time?",
#     "Have you taken any treatment or medicine for this problem?",
# ]

QUESTIONS =[
    "आज आपको क्या तकलीफ़ है?",
    # "यह तकलीफ़ कब से है?",
    # "अभी यह तकलीफ़ कितनी ज़्यादा है?",
    # "समय के साथ यह तकलीफ़ कैसी हुई है?",
    # "क्या आपने इसके लिए कोई इलाज या दवा ली है?"
]


class InterviewState:

    def __init__(self, call_sid: str):

        self.call_sid = call_sid

        self.current_question = 0

        self.responses = []

        self.goodbye_sent = False

    def current_question_text(self):

        return QUESTIONS[self.current_question]

    def save_answer(self, answer: str):

        self.responses.append(
            {
                "question": QUESTIONS[self.current_question],
                "answer": answer
            }
        )

        self.current_question += 1

    def completed(self):

        return self.current_question >= len(QUESTIONS)