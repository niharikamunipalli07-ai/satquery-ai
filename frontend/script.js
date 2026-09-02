// ==========================================
// SATQUERY AI - FRONTEND
// ==========================================

const API_URL = "";

let uploadedFilename = null;


// ==========================================
// HTML ELEMENTS - SINGLE IMAGE
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
// HTML ELEMENTS - CHANGE DETECTION
// ==========================================

const beforeInput = document.getElementById("beforeInput");
const afterInput = document.getElementById("afterInput");

const beforePreview = document.getElementById("beforePreview");
const afterPreview = document.getElementById("afterPreview");

const beforeStatus = document.getElementById("beforeStatus");
const afterStatus = document.getElementById("afterStatus");

const changeQuestion = document.getElementById("changeQuestion");
const changeButton = document.getElementById("changeButton");

const changeStatus = document.getElementById("changeStatus");

const changePercentage =
    document.getElementById("changePercentage");

const changeAnswer =
    document.getElementById("changeAnswer");

const changeVisualization =
    document.getElementById("changeVisualization");


// ==========================================
// SINGLE IMAGE PREVIEW
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
// SINGLE IMAGE UPLOAD
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
// ASK SINGLE IMAGE QUESTION
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

        category.innerText =
            data.category ||
            "VQA";

        plannerReason.innerText =
            data.planner_reason ||
            "Satellite image analysis completed.";

        if (data.answer) {

            answer.innerText =
                data.answer;

        } else if (
            data.geo_information &&
            data.geo_information.answer
        ) {

            answer.innerText =
                data.geo_information.answer;

        } else if (data.geo_information) {

            answer.innerText =
                JSON.stringify(
                    data.geo_information,
                    null,
                    2
                );

        } else {

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


// ==========================================
// BEFORE IMAGE PREVIEW
// ==========================================

beforeInput.addEventListener(
    "change",
    function () {

        const file =
            beforeInput.files[0];

        if (!file) {
            return;
        }

        beforePreview.src =
            URL.createObjectURL(file);

        beforePreview.style.display =
            "block";

        beforeStatus.innerText =
            "✅ Before image selected: " +
            file.name;

        updateChangeButton();

    }
);


// ==========================================
// AFTER IMAGE PREVIEW
// ==========================================

afterInput.addEventListener(
    "change",
    function () {

        const file =
            afterInput.files[0];

        if (!file) {
            return;
        }

        afterPreview.src =
            URL.createObjectURL(file);

        afterPreview.style.display =
            "block";

        afterStatus.innerText =
            "✅ After image selected: " +
            file.name;

        updateChangeButton();

    }
);


// ==========================================
// ENABLE CHANGE BUTTON
// ==========================================

function updateChangeButton() {

    const beforeFile =
        beforeInput.files[0];

    const afterFile =
        afterInput.files[0];

    if (beforeFile && afterFile) {

        changeButton.disabled =
            false;

        changeStatus.innerText =
            "✅ Both images selected. Ready for analysis.";

    } else {

        changeButton.disabled =
            true;

        changeStatus.innerText =
            "Select both images to begin.";

    }
}


// ==========================================
// CHANGE DETECTION
// ==========================================

changeButton.addEventListener(
    "click",
    async function () {

        const beforeFile =
            beforeInput.files[0];

        const afterFile =
            afterInput.files[0];

        if (!beforeFile || !afterFile) {

            changeStatus.innerText =
                "❌ Please select both images.";

            return;
        }

        let userQuestion =
            changeQuestion.value.trim();

        if (!userQuestion) {

            userQuestion =
                "What changed between these two satellite images?";

        }

        changeButton.disabled =
            true;

        changeStatus.innerText =
            "⏳ SatQuery AI is comparing both satellite images...";

        changePercentage.innerText =
            "Processing...";

        changeAnswer.innerText =
            "🤖 Analyzing changes between T1 and T2...";

        changeVisualization.style.display =
            "none";

        try {

            const formData =
                new FormData();

            formData.append(
                "before",
                beforeFile
            );

            formData.append(
                "after",
                afterFile
            );

            const url =
                API_URL +
                "/change-detection?question=" +
                encodeURIComponent(
                    userQuestion
                );

            const response =
                await fetch(
                    url,
                    {
                        method: "POST",
                        body: formData
                    }
                );

            const responseText =
                await response.text();

            console.log(
                "CHANGE DETECTION RAW RESPONSE:",
                responseText
            );

            let data;

            try {

                data =
                    JSON.parse(
                        responseText
                    );

            } catch {

                throw new Error(
                    "Backend returned an invalid response."
                );

            }

            console.log(
                "CHANGE DETECTION RESPONSE:",
                data
            );

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    data.error ||
                    "Change detection failed."
                );

            }

            if (!data.success) {

                throw new Error(
                    data.answer ||
                    "Change detection failed."
                );

            }

            // ======================================
            // CHANGE PERCENTAGE
            // ======================================

            if (
                data.change_percentage !==
                undefined
            ) {

                changePercentage.innerText =
                    data.change_percentage +
                    "%";

            } else {

                changePercentage.innerText =
                    "Not available";

            }


            // ======================================
            // AI ANSWER
            // ======================================

            changeAnswer.innerText =
                data.answer ||
                "No AI interpretation returned.";


            // ======================================
            // VISUALIZATION
            // ======================================

            if (data.visualization) {

                let visualizationPath =
                    data.visualization;

                /*
                 * Backend currently returns:
                 * outputs/changes/...
                 *
                 * Convert it into a browser URL.
                 */

                visualizationPath =
                    visualizationPath
                    .replaceAll("\\", "/");

                if (
                    visualizationPath.startsWith(
                        "outputs/"
                    )
                ) {

                    visualizationPath =
                        "/" +
                        visualizationPath;

                }

                changeVisualization.src =
                    visualizationPath;

                changeVisualization.style.display =
                    "block";

            }


            changeStatus.innerText =
                "✅ Change detection completed successfully.";

        } catch (error) {

            console.error(
                "CHANGE DETECTION ERROR:",
                error
            );

            changeStatus.innerText =
                "❌ Change detection failed.";

            changePercentage.innerText =
                "Error";

            changeAnswer.innerText =
                error.message;

        } finally {

            changeButton.disabled =
                false;

            updateChangeButton();

        }

    }
);