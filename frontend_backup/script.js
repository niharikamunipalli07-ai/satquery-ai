const API_URL = "http://127.0.0.1:8000";

let uploadedFilename = null;

const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const uploadButton = document.getElementById("uploadButton");
const uploadStatus = document.getElementById("uploadStatus");
const askButton = document.getElementById("askButton");
const question = document.getElementById("question");
const result = document.getElementById("result");


// IMAGE PREVIEW
imageInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) {
        return;
    }

    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";

    uploadStatus.textContent = "Image selected. Click Upload Image.";
});


// UPLOAD IMAGE
uploadButton.addEventListener("click", async function (event) {

    event.preventDefault();

    const file = imageInput.files[0];

    if (!file) {
        uploadStatus.textContent = "❌ Please select an image first.";
        return;
    }

    uploadStatus.textContent = "⏳ Uploading image...";
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

        const data = await response.json();

        console.log("UPLOAD RESPONSE:", data);

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed");
        }

        uploadedFilename = data.filename;

        uploadStatus.textContent =
            "✅ Image uploaded successfully!";

    } catch (error) {

        console.error("UPLOAD ERROR:", error);

        uploadStatus.textContent =
            "❌ Upload failed: " + error.message;

    } finally {

        uploadButton.disabled = false;
    }
});


// ASK VQA
askButton.addEventListener("click", async function (event) {

    event.preventDefault();

    if (!uploadedFilename) {

        result.textContent =
            "❌ Please upload an image first.";

        return;
    }

    const userQuestion = question.value.trim();

    if (!userQuestion) {

        result.textContent =
            "❌ Please enter a question.";

        return;
    }

    result.textContent =
        "🤖 SatQuery AI is analyzing the image...";

    askButton.disabled = true;

    try {

        const response = await fetch(
            API_URL + "/vqa",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    filename: uploadedFilename,
                    question: userQuestion
                })
            }
        );

        const data = await response.json();

        console.log("VQA RESPONSE:", data);

        if (!response.ok) {
            throw new Error(data.detail || "VQA failed");
        }

        result.textContent = data.answer;

    } catch (error) {

        console.error("VQA ERROR:", error);

        result.textContent =
            "❌ " + error.message;

    } finally {

        askButton.disabled = false;
    }
});