// ==========================================
// SATQUERY AI - FRONTEND
// ==========================================


// Render and local development both work
// because the API uses the same website.

const API_URL = "";


// Uploaded image filename
let uploadedFilename = null;


// ==========================================
// GET ELEMENTS
// ==========================================

const imageInput =
    document.getElementById("imageInput");

const preview =
    document.getElementById("preview");

const uploadButton =
    document.getElementById("uploadButton");

const uploadStatus =
    document.getElementById("uploadStatus");

const askButton =
    document.getElementById("askButton");

const questionInput =
    document.getElementById("questionInput");

const category =
    document.getElementById("category");

const plannerReason =
    document.getElementById("plannerReason");

const answer =
    document.getElementById("answer");


// ==========================================
// IMAGE PREVIEW
// ==========================================

imageInput.addEventListener(
    "change",
    function () {

        const file =
            imageInput.files[0];

        if (!file) {
            return;
        }

        preview.src =
            URL.createObjectURL(file);

        preview.style.display =
            "block";

        uploadStatus.textContent =
            "Image selected: " +
            file.name;

        uploadStatus.className = "";

        askButton.disabled = true;
    }
);


// ==========================================
// UPLOAD IMAGE
// ==========================================

uploadButton.addEventListener(
    "click",
    async function () {

        const file =
            imageInput.files[0];

        if (!file) {

            uploadStatus.textContent =
                "❌ Please select an image first.";

            uploadStatus.className =
                "error";

            return;
        }


        uploadButton.disabled = true;

        uploadStatus.textContent =
            "⏳ Uploading image...";

        uploadStatus.className = "";


        try {

            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );


            const response =
                await fetch(
                    API_URL + "/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const responseText =
                await response.text();


            console.log(
                "UPLOAD RESPONSE:",
                responseText
            );


            let data;


            try {

                data =
                    JSON.parse(responseText);

            }
            catch {

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


            uploadStatus.textContent =
                "✅ Image uploaded successfully!";

            uploadStatus.className =
                "success";


            askButton.disabled =
                false;


        }
        catch (error) {

            console.error(
                "UPLOAD ERROR:",
                error
            );


            uploadStatus.textContent =
                "❌ " +
                error.message;

            uploadStatus.className =
                "error";


            askButton.disabled =
                true;

        }
        finally {

            uploadButton.disabled =
                false;
        }

    }
);


// ==========================================
// ASK SATQUERY AI
// ==========================================

askButton.addEventListener(
    "click",
    async function () {

        if (!uploadedFilename) {

            answer.textContent =
                "❌ Please upload an image first.";

            return;
        }


        const userQuestion =
            questionInput.value.trim();


        if (!userQuestion) {

            answer.textContent =
                "❌ Please enter a question.";

            return;
        }


        askButton.disabled = true;


        category.textContent =
            "Processing...";


        plannerReason.textContent =
            "Processing your question...";


        answer.textContent =
            "🤖 SatQuery AI is analyzing the image...";


        try {

            const response =
                await fetch(
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

                data =
                    JSON.parse(responseText);

            }
            catch {

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
                    "AI request failed."
                );
            }


            // ==================================
            // CATEGORY
            // ==================================

            category.textContent =
                data.category ||
                "Unknown";


            // ==================================
            // PLANNER
            // ==================================

            plannerReason.textContent =
                data.planner_reason ||
                "No planner information returned.";


            // ==================================
            // ANSWER
            // ==================================

            let finalAnswer = "";


            // VQA / ANALYSIS
            if (data.answer) {

                finalAnswer =
                    data.answer;
            }


            // GEO
            else if (
                data.geo_information
            ) {

                const geo =
                    data.geo_information;


                if (geo.answer) {

                    finalAnswer =
                        geo.answer;

                }
                else {

                    finalAnswer =
                        JSON.stringify(
                            geo,
                            null,
                            2
                        );
                }
            }


            // Nothing returned
            else {

                finalAnswer =
                    "⚠️ No answer returned.\n\n" +
                    JSON.stringify(
                        data,
                        null,
                        2
                    );
            }


            answer.textContent =
                finalAnswer;


        }
        catch (error) {

            console.error(
                "VQA ERROR:",
                error
            );


            answer.textContent =
                "❌ " +
                error.message;

        }
        finally {

            askButton.disabled =
                false;
        }

    }
);