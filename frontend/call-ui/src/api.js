import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export const triggerCall = async (phoneNumber) => {
    const response = await axios.post(
        `${API_BASE_URL}/trigger-call`,
        {
            phone_number: phoneNumber,
        }
    );

    return response.data;
};

export const getCallResult = async (callSid) => {
    const response = await axios.get(
        `${API_BASE_URL}/call-results/${callSid}`
    );

    return response.data;
};