// ==========================================
// SATQUERY AI - FRONTEND SCRIPT
// ==========================================

// IMPORTANT:
// Empty string means use the same Render website
// instead of localhost.
const API_URL = "";

let uploadedFilename = null;


// ==========================================
// GET HTML ELEMENTS
// ==========================================

const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const uploadButton = document.getElementById("uploadButton");
const uploadStatus = document.getElementById("uploadStatus");

const askButton = document.getElementById("askButton");
const question = document.getElementById("question");
const result = document.getElementById("result");


// ==========================================
// IMAGE PREVIEW
// ==========================================

imageInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) {
        return;
    }

    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";

    uploadStatus.textContent =
        "Image selected. Click Upload Image.";
});


// ==========================================
// UPLOAD IMAGE
// ==========================================

uploadButton.addEventListener("click", async function (event) {

    event.preventDefault();

    const file = imageInput.files[0];

    if (!file) {

        uploadStatus.textContent =
            "❌ Please select an image first.";

        return;
    }

    uploadStatus.textContent =
        "⏳ Uploading image...";

    uploadButton.disabled = true;

    const formData = new FormData();

    formData.append("file", file);


    try {

        const response = await fetch(
            API_URL + "/upload",
            {
                method: "POST",
                body: formData
            }
        );


        // Read response as TEXT first
        const responseText =
            await response.text();

        console.log(
            "UPLOAD RAW RESPONSE:",
            responseText
        );


        // Convert to JSON safely
        let data;

        try {

            data = JSON.parse(responseText);

        } catch (jsonError) {

            throw new Error(
                "Server returned an invalid response: " +
                responseText
            );
        }


        console.log(
            "UPLOAD RESPONSE:",
            data
        );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                "Upload failed"
            );
        }


        // Save filename
        uploadedFilename =
            data.filename;


        if (!uploadedFilename) {

            throw new Error(
                "Server did not return an uploaded filename."
            );
        }


        uploadStatus.textContent =
            "✅ Image uploaded successfully!";


    } catch (error) {

        console.error(
            "UPLOAD ERROR:",
            error
        );

        uploadStatus.textContent =
            "❌ Upload failed: " +
            error.message;


    } finally {

        uploadButton.disabled = false;
    }

});


// ==========================================
// ASK SATQUERY AI
// ==========================================

askButton.addEventListener("click", async function (event) {

    event.preventDefault();


    // Check image
    if (!uploadedFilename) {

        result.textContent =
            "❌ Please upload an image first.";

        return;
    }


    // Get question
    const userQuestion =
        question.value.trim();


    if (!userQuestion) {

        result.textContent =
            "❌ Please enter a question.";

        return;
    }


    // Show processing
    result.textContent =
        "🤖 SatQuery AI is analyzing the image...";

    askButton.disabled = true;


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


        // ==================================
        // READ RESPONSE SAFELY
        // ==================================

        const responseText =
            await response.text();


        console.log(
            "VQA RAW RESPONSE:",
            responseText
        );


        let data;


        try {

            data =
                JSON.parse(responseText);

        } catch (jsonError) {

            throw new Error(
                "Backend returned an invalid response: " +
                responseText
            );
        }


        console.log(
            "VQA RESPONSE:",
            data
        );


        // ==================================
        // HANDLE SERVER ERROR
        // ==================================

        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.error ||
                "VQA request failed"
            );
        }


        // ==================================
        // DISPLAY AI ANSWER
        // ==================================

        if (data.answer) {

            result.textContent =
                data.answer;

        }

        else if (data.geo_information) {

            result.textContent =
                JSON.stringify(
                    data.geo_information,
                    null,
                    2
                );

        }

        else {

            result.textContent =
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


        result.textContent =
            "❌ " +
            error.message;


    } finally {

        askButton.disabled = false;
    }

});