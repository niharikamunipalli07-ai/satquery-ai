// ==========================================
// SATQUERY AI - FRONTEND
// ==========================================

// Empty string = use the same Render website
const API_URL = "";

let uploadedFilename = null;


// ==========================================
// HTML ELEMENTS
// ==========================================

const imageInput = document.getElementById("imageInput");
const uploadButton = document.getElementById("uploadButton");
const uploadStatus = document.getElementById("uploadStatus");
const preview = document.getElementById("preview");

const questionInput = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");

const category = document.getElementById("category");
const plannerReason = document.getElementById("plannerReason");
const answer = document.getElementById("answer");


// ==========================================
// IMAGE PREVIEW
// ==========================================

imageInput.addEventListener("change", function () {

    const file = imageInput.files[0];

    if (!file) {
        return;
    }

    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";

    uploadStatus.innerText =
        "Image selected: " + file.name;

    uploadStatus.className = "status";
});


// ==========================================
// UPLOAD IMAGE
// ==========================================

uploadButton.addEventListener("click", async function () {

    const file = imageInput.files[0];

    if (!file) {

        uploadStatus.innerText =
            "❌ Please select an image first.";

        return;
    }

    uploadButton.disabled = true;

    uploadStatus.innerText =
        "⏳ Uploading image...";

    try {

        const formData = new FormData();

        formData.append("file", file);


        const response = await fetch(
            API_URL + "/upload",
            {
                method: "POST",
                body: formData
            }
        );


        const responseText =
            await response.text();

        console.log(
            "UPLOAD RAW RESPONSE:",
            responseText
        );


        let data;

        try {

            data = JSON.parse(responseText);

        } catch {

            throw new Error(
                "Server returned an invalid response."
            );
        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                "Image upload failed."
            );
        }


        uploadedFilename =
            data.filename;


        if (!uploadedFilename) {

            throw new Error(
                "Backend did not return a filename."
            );
        }


        uploadStatus.innerText =
            "✅ Image uploaded successfully!";


        askButton.disabled = false;


        category.innerText =
            "Waiting...";

        plannerReason.innerText =
            "Ready to analyze your question.";

        answer.innerText =
            "Image uploaded. Ask a question about it.";


    } catch (error) {

        console.error(
            "UPLOAD ERROR:",
            error
        );

        uploadStatus.innerText =
            "❌ " + error.message;

        askButton.disabled = true;


    } finally {

        uploadButton.disabled = false;

    }

});


// ==========================================
// ASK QUESTION
// ==========================================

askButton.addEventListener("click", async function () {

    if (!uploadedFilename) {

        answer.innerText =
            "❌ Please upload an image first.";

        return;
    }


    const userQuestion =
        questionInput.value.trim();


    if (!userQuestion) {

        answer.innerText =
            "❌ Please enter a question.";

        return;
    }


    askButton.disabled = true;


    category.innerText =
        "Processing...";

    plannerReason.innerText =
        "Processing your question...";

    answer.innerText =
        "🤖 SatQuery AI is analyzing the satellite image...";


    try {

        const response = await fetch(
            API_URL + "/vqa",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    filename:
                        uploadedFilename,

                    question:
                        userQuestion

                })
            }
        );


        const responseText =
            await response.text();


        console.log(
            "VQA RAW RESPONSE:",
            responseText
        );


        let data;

        try {

            data = JSON.parse(responseText);

        } catch {

            throw new Error(
                "Backend returned an invalid response."
            );
        }


        console.log(
            "VQA RESPONSE:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                "VQA request failed."
            );
        }


        // ======================================
        // CATEGORY
        // ======================================

        category.innerText =
            data.category ||
            "VQA";


        // ======================================
        // PLANNER
        // ======================================

        plannerReason.innerText =
            data.planner_reason ||
            "Satellite image analysis completed.";


        // ======================================
        // AI ANSWER
        // ======================================

        if (data.answer) {

            answer.innerText =
                data.answer;

        }

        else if (
            data.geo_information &&
            data.geo_information.answer
        ) {

            answer.innerText =
                data.geo_information.answer;

        }

        else if (data.geo_information) {

            answer.innerText =
                JSON.stringify(
                    data.geo_information,
                    null,
                    2
                );

        }

        else {

            answer.innerText =
                "⚠️ No answer returned.\n\n" +
                JSON.stringify(
                    data,
                    null,
                    2
                );
        }


    } catch (error) {

        console.error(
            "VQA ERROR:",
            error
        );

        answer.innerText =
            "❌ " + error.message;

    } finally {

        askButton.disabled = false;

    }

});