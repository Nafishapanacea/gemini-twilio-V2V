import axios from "axios";

// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
const API_BASE_URL = "https://omen.radpretation.ai/gemini-twilio-telephony"

export const triggerCall = async (phoneNumber) => {
    const response = await axios.post(
        `${API_BASE_URL}/trigger-call`,
        {
            phone_number: phoneNumber,
        }
    );

    return response.data;
};

export const getCallResult = async (callSid, wait = false) => {
    const response = await axios.get(
        `${API_BASE_URL}/call-results/${callSid}`,
        {
            params: wait ? { wait: true } : {}
        }
    );

    return response.data;
};