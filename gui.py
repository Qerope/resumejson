import gradio as gr
import json
import subprocess
import os
from cohere import ClientV2

# Initialize Cohere API
cohere_api_key = "39TAyPgeBqHh9rFoQLDtZL26dluSbjIqBBtjHnEa"  # Replace with your actual API key securely in production
cohere_client = ClientV2(api_key=cohere_api_key)

# Function to summarize the job description and extract keywords
def summarize_job(job_description):
        responseFormat = {
            "type": "json_object", 
            "json_schema": {
                "type": "object", 
                "properties": {
                    "job_title": { "type": "string" }, 
                    "job_requirements": { "type": "string" }, 
                    "job_keywords": { "type": "string" }, 
                    "job_shortname": { "type": "string" }
                }, 
                "required": ["job_title", "job_requirements", "job_keywords", "job_shortname"]
            }
        }
        # Call Cohere API to summarize job description
        response = cohere_client.chat(
            messages=[
                { "role": "system", "content": "Generate a JSON formatted {job_title: String, job_requirements: String, job_keywords: String, job_shortname: String} for the provided job description. job_shortname must only include lowecase letters and underscores maximum 3 parts.job_keywords must include everything. job_requirements must includ recommanded." }, 
                { "role": "user", "content": job_description }
                ],
            response_format=responseFormat,
            safety_mode="OFF",
            model="command-r-plus-08-2024"
        )

        print(response.message.content[0].text)

        jobdet = json.loads(response.message.content[0].text)

        jobtitle = jobdet['job_title']
        requirements = jobdet['job_requirements']
        keywords = jobdet['job_keywords']
        shortname = f"resume_{jobdet['job_shortname']}"

        return {"title": jobtitle, "requirements": requirements, "keywords": keywords, "shortname": shortname}

def generate_resume_data(resume_data, job_data):
        responseFormat = {
            "type": "json_object", 
            "json_schema": {
                "type": "object",
                "properties": {
                    "work": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "name": { "type": "string" },
                        "position": { "type": "string" },
                        "startDate": { "type": "string", "format": "date" },
                        "endDate": { "type": "string", "format": "date" },
                        "summary": { "type": "string" }
                        },
                        "required": ["name", "position", "startDate", "endDate", "summary"]
                    }
                    },
                    "volunteer": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "organization": { "type": "string" },
                        "position": { "type": "string" },
                        "startDate": { "type": "string", "format": "date" },
                        "endDate": { "type": "string", "format": "date" }
                        },
                        "required": ["organization", "position", "startDate", "endDate"]
                    }
                    },
                    "education": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "institution": { "type": "string" },
                        "area": { "type": "string" },
                        "studyType": { "type": "string" },
                        "startDate": { "type": "string", "format": "date" },
                        "endDate": { "type": "string", "format": "date" }
                        },
                        "required": ["institution", "area", "studyType", "startDate", "endDate"]
                    }
                    },
                    "awards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "title": { "type": "string" },
                        "date": { "type": "string", "format": "date" },
                        "awarder": { "type": "string" }
                        },
                        "required": ["title", "date", "awarder"]
                    }
                    },
                    "certificates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "name": { "type": "string" },
                        "issuer": { "type": "string" }
                        },
                        "required": ["name", "issuer"]
                    }
                    },
                    "publications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "name": { "type": "string" },
                        "releaseDate": { "type": "string", "format": "date" },
                        "url": { "type": "string" }
                        },
                        "required": ["name", "releaseDate", "url"]
                    }
                    },
                    "skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "name": { "type": "string" },
                        "keywords": {
                            "type": "array",
                            "items": { "type": "string" }
                        }
                        },
                        "required": ["name", "keywords"]
                    }
                    },
                    "projects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "name": { "type": "string" },
                        "startDate": { "type": "string", "format": "date" },
                        "endDate": { "type": "string", "format": "date" },
                        "description": { "type": "string" },
                        "url": { "type": "string" }
                        },
                        "required": ["name", "startDate", "endDate", "description", "url"]
                    }
                    }
                },
                "required": [
                    "work",
                    "volunteer",
                    "education",
                    "awards",
                    "certificates",
                    "publications",
                    "skills",
                    "projects"
                ]
            }
        }
        # Call Cohere API to summarize job description
        response = cohere_client.chat(
            messages=[
                { "role": "system", "content": "Generate a JSON tailoured resume for the provided job data using the provided resume data." }, 
                { "role": "user", "content": str(job_data) },
                { "role": "user", "content": resume_data }
                ],
            response_format=responseFormat,
            safety_mode="OFF",
            model="command-r-plus-08-2024"
        )

        os.makedirs("./output/data", exist_ok=True)
        output_json_path = f"./output/data/{job_data['shortname']}.json"
        with open(output_json_path, 'w') as f:
            f.write(response.message.content[0].text)
        resdet = json.loads(response.message.content[0].text)

        return resdet

# Function to generate a tailored resume
def generate_resume(cv_file_org, cv_data_raw, job_data):
    cv_file_data = {}

    with open(cv_file_org, 'w') as f:
        json.dump(cv_file_data, f)

    tailored_resume = generate_resume_data(cv_data_raw, job_data)

    for key in tailored_resume:
        if key in cv_file_data:
            cv_file_data[key] = tailored_resume[key]

    os.makedirs("./output/json", exist_ok=True)
    os.makedirs("./output/html", exist_ok=True)

    output_json_path = f"./output/json/{job_data['shortname']}.json"
    with open(output_json_path, 'w') as f:
        json.dump(tailored_resume, f, indent=2)

    # Convert to HTML using jsonresume CLI
    output_html_path = f"./output/html/{job_data['shortname']}.html"
    subprocess.run([
        "resume", "export", output_html_path,
        "--resume", output_json_path,
        "--theme", "stackoverflow-crewshin"
    ], check=True)

    return output_html_path

# Function to display HTML content
def display_html(file_path):
    try:
        with open(file_path, 'r') as f:
            html_content = f.read()
        return html_content
    except Exception as e:
        return f"Error reading HTML file: {str(e)}"

# Gradio interface
def main_interface():
    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                cv_file = gr.File(label="Resume Data", type="filepath")
                cv_data = gr.Textbox(label="Resume Data", lines=5)
            job_description = gr.Textbox(label="Job Description", lines=10)
            summarize_btn = gr.Button("Summarize Job Description")
        with gr.Row():
            job_data_display = gr.JSON(label="Extracted Job Data")
            generate_resume_btn = gr.Button("Generate Resume")
        
        with gr.Row():
            html_display = gr.HTML(label="Generated Resume")
        
        # Event handlers
        def on_summarize(job_desc):
            return summarize_job(job_desc)

        def on_generate_resume(file, resume_data, job_data):
            if not file:
                return "Please upload a JSON resume file."
            base_json_path = file.name
            return display_html(generate_resume(base_json_path, resume_data, job_data))

        summarize_btn.click(on_summarize, inputs=[job_description], outputs=[job_data_display])
        generate_resume_btn.click(on_generate_resume, inputs=[cv_file, cv_data, job_data_display], outputs=[html_display])

    return demo

# Launch the app
if __name__ == "__main__":
    main_interface().launch()
