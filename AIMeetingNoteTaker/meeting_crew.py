# meeting_crew.py
from crewai import Agent, Task, Crew, Process, LLM
from tools import search_gmail, read_email, send_email, create_draft
import os
from dotenv import load_dotenv
import logging
from langfuse import get_client
import openlit

# Load environment variables from .env file
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
 
# Get keys for your project from the project settings page: https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY") 
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST") 
 
langfuse = get_client()
 
# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

 
# Initialize OpenLIT instrumentation. The disable_batch flag is set to true to process traces immediately. Also set the langfuse tracer to use the langfuse tracer.
openlit.init(tracer=langfuse._otel_tracer, disable_batch=True)


def run_crew_analysis(meeting_transcript_text: str) -> dict:
    """
    Initializes and runs the CrewAI process.
    Returns the direct output from key tasks.
    """
    # --- LLM Configuration ---
    llm = LLM(
        model="gemini/gemini-2.0-flash",
        provider="google",
        api_key=GOOGLE_API_KEY
    )


    # Gmail tools list
    tools_list = [search_gmail, read_email, send_email, create_draft]


    # --- Define the Agents ---
    # Agent 1: Meeting Analyst
    meeting_analyst = Agent(
        role='Senior Meeting Analyst',
        goal='Extract and understand the core content, themes, and structure of meeting transcripts',
        backstory="""You are an expert at analyzing meeting transcripts with years of experience 
        in corporate environments. You have a keen eye for identifying key discussion points, 
        decision-making moments, and important details that need to be captured.""",
        verbose=True,
        allow_delegation=False,
        llm = llm
    )

    # Agent 2: Action Item Specialist
    action_item_specialist = Agent(
        role='Action Item Specialist',
        goal='Identify and structure actionable tasks from meeting discussions',
        backstory="""You specialize in converting meeting discussions into clear, actionable items. 
        You have extensive experience in project management and know how to extract commitments, 
        deadlines, and responsibilities from conversational text. You ensure no important task 
        is overlooked.""",
        verbose=True,
        allow_delegation=False,
        llm = llm

    )

    # Agent 3: Content Organizer
    content_organizer = Agent(
        role='Content Organization Expert',
        goal='Structure meeting content into logical, hierarchical outlines',
        backstory="""You are an expert at organizing information into clear, logical structures. 
        With a background in technical writing and information architecture, you excel at 
        creating hierarchical outlines that make complex discussions easy to follow and reference.""",
        verbose=True,
        allow_delegation=False,
        llm = llm
    )

    # Agent 4: Quality Assurance Editor
    qa_editor = Agent(
        role='Quality Assurance Editor',
        goal='Ensure meeting notes are comprehensive, accurate, and well-formatted',
        backstory="""You are a meticulous editor with years of experience in corporate documentation. 
        You ensure that meeting notes are complete, accurate, professional, and follow consistent 
        formatting standards. You catch details others might miss and ensure the final output 
        meets high-quality standards.""",
        verbose=True,
        allow_delegation=False,
        llm = llm
    )

    # Agent 5: The Strategist 
    strategist_agent = Agent(
        role="Meeting Analysis Strategist",
        goal="Analyze meeting transcripts to determine optimal documentation frameworks based on meeting type, participants, and discussion patterns.",
        backstory=(
            "You are a renowned organizational psychology consultant specializing in meeting effectiveness and documentation strategies. "
            "You can instantly identify meeting types (status updates, brainstorming sessions, decision-making meetings, interviews, etc.) "
            "and prescribe the most effective documentation framework for each. Your strategies are based on cognitive science research "
            "about how people process and retain information from different types of discussions."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # Agent 6: The Synthesizer
    synthesizer_agent = Agent(
        role="Strategic Note Curator",
        goal="Apply sophisticated note-taking methodologies to transform raw meeting transcripts into structured, actionable documentation.",
        backstory=(
            "You are an expert knowledge manager who specializes in information architecture and strategic documentation. "
            "You excel at following complex documentation frameworks while maintaining the essence and nuance of discussions. "
            "Your notes are known for their clarity, completeness, and actionability. You understand how to balance comprehensiveness "
            "with conciseness, ensuring that every stakeholder gets the information they need in the format they can best use."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # Agent 7: Email Assistant
    email_assistant = Agent(
        role="Meeting Minutes Distribution Specialist",
        goal="Format and distribute meeting minutes via email to relevant stakeholders",
        backstory=
        """You are a professional communication specialist with expertise in corporate 
        correspondence and meeting minute distribution. You excel at formatting meeting notes 
        for email distribution, crafting professional subject lines, and ensuring the right 
        people receive the appropriate information. You understand the importance of clear, 
        concise communication and follow corporate email etiquette standards."""
        ,
        tools=tools_list,
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
 

    # --- Define the Tasks with Enhanced Prompts ---
    # Task 1: Analyze Meeting Content
    analyze_meeting_task = Task(
        description="""Analyze the provided meeting transcript and extract:
        1. Main topics and themes discussed
        2. Key participants and their roles
        3. Important decisions made
        4. Discussion flow and structure
        5. Meeting context and purpose
        
        Focus on understanding the overall meeting dynamics and identifying the most important content.
        
        Meeting Transcript: {meeting_transcript}""",
        expected_output="Detailed analysis of meeting content including main themes, participants, decisions, and structure",
        agent=meeting_analyst
    )

    # Task 2: Extract Action Items
    extract_action_items_task = Task(
        description="""Based on the meeting analysis provided in the context, extract and structure all action items.
        
        For each action item:
        - Provide a clear, concise description of what needs to be done
        - Identify who is responsible (if mentioned)
        - Note any deadlines or timeframes
        - Include relevant context or dependencies
        
        Format action items as a bulleted list with clear, actionable language.
        Ensure items are specific enough to be tracked and completed.""",
        expected_output="A structured list of action items with clear descriptions, responsibilities, and deadlines.",
        agent=action_item_specialist,
        context=[analyze_meeting_task]
    )

    # Task 3: Create Detailed Outline
    create_outline_task = Task(
        description="""Using the meeting analysis from the context, create a detailed, hierarchical outline of the meeting content.
        
        Use main sections with descriptive titles, then break down into:
        - Key discussion points
        - Important details and context
        - Decisions made
        - Next steps mentioned
        
        Organize content logically and chronologically where appropriate.
        Use clear, descriptive headers and subheaders.""",
        expected_output="A well-structured hierarchical outline of the meeting's content.",
        agent=content_organizer,
        context=[analyze_meeting_task]
    )

    # Task 4: Compile and Review Final Notes
    compile_notes_task = Task(
        description="""Compile the final meeting notes using the analysis, action items, and outline provided in the context.
        
        Structure the final output as follows:
        
        # Meeting Notes
        
        ## Overview
        [A comprehensive summary paragraph covering the meeting's purpose, key outcomes, and significance.]
        
        ## Action Items
        [The formatted list of action items.]
        
        ## Detailed Outline
        [The hierarchical breakdown of meeting content.]
        
        Ensure the final document is professional, consistent, complete, accurate, and easy to read.
        Check for proper grammar and spelling.""",
        expected_output="A single, complete, and professionally formatted Markdown document containing the meeting overview, action items, and detailed outline.",
        output_file="Meeting_Notes.md",
        agent=qa_editor,
        context=[analyze_meeting_task, extract_action_items_task, create_outline_task]
    )
    # Task 5: Design the note-taking template
    strategy_creation_task = Task(
        description=(
            "1. Analyze the following meeting transcript to identify its primary type (e.g., Progress Update, Brainstorming, 1-on-1, Interview).\n"
            "2. Based on this type, create a detailed, actionable note-taking strategy. This strategy must be a clear set of instructions for another agent.\n"
            "3. The strategy should outline the key sections to create (like 'Decisions Made', 'Action Items', 'Key Blockers') and what specific information to extract for each section.\n\n"
            "Here is the transcript:\n---\n{meeting_transcript}\n---"
        ),
        agent=strategist_agent,
        expected_output="A text document containing both the meeting type analysis and the detailed note-taking strategy with clear sections and instructions.",
    )

    # Task 6: Generate the Notes
    note_generation_task = Task(
        description=(
            "Using the note-taking strategy provided in the context, process the full meeting transcript and generate the final notes. "
            "Follow the strategy precisely. Format the output clearly in Markdown. "
            "Ensure each action item includes WHO is responsible and WHAT they need to do.\n\n"
            "Here is the full transcript for your reference:\n---\n{meeting_transcript}\n---"
        ),
        agent=synthesizer_agent,
        expected_output="A final, well-structured document of the meeting notes in Markdown format, perfectly following the provided strategy.",
        context=[strategy_creation_task],
        markdown=True,
        output_file="Meeting_Notes2.md"
    )

    # Task 8: Draft the MoM Email
    task_draft_email = Task(
        description=(
            "1. Read and synthesize the final meeting notes from the two generated files: 'Meeting_Notes.md' and 'Meeting_Notes2.md'.\n"
            "2. Create a professional Minutes of Meeting (MoM) email draft based on these notes.\n"
            "3. Write a suitable email subject which includes MoM'.\n"
            "4. Use the 'Create Email Draft' tool to save this email in Gmail. Set the recipient ('to') as 'team@example.com'.\n"

            "**IMPORTANT**: The notes are in Markdown format. You MUST convert all Markdown syntax "
            "(like `###` headers, `**bold**`, and `*` or `-` list items) into a clean, professional, plain-text format "
            "suitable for an email body. Do not include any raw markdown characters like `*` or `#` in the final email body."
        ),
        expected_output="Email Draft Content and a confirmation message from the Gmail tool indicating that the draft was successfully created, including the draft ID.",
        agent=email_assistant,
        context=[compile_notes_task, note_generation_task] # This task runs only after both note files are created.
    )

    # --- Crew Definition and Execution ---
    
    with langfuse.start_as_current_span(name="crewai-index-trace"):
        meeting_crew = Crew(
            agents=[meeting_analyst, action_item_specialist, content_organizer, qa_editor, strategist_agent, synthesizer_agent, email_assistant],
            tasks=[analyze_meeting_task, extract_action_items_task, create_outline_task, compile_notes_task, strategy_creation_task, note_generation_task, task_draft_email],
            process=Process.sequential,
            verbose=True
        )
    langfuse.flush()

    # Run the crew
    crew_result = meeting_crew.kickoff(inputs={'meeting_transcript': meeting_transcript_text})
    logging.info(f"crew_result: {crew_result}")
    logging.info(f"note_generation_task.output: {note_generation_task.output}")
    logging.info(f"task_draft_email.output: {task_draft_email.output.raw}")
    # --- Return Raw Outputs Directly from Tasks ---
    # The `raw` attribute holds the final string result of the task.
    results = {
        "compiled_notes": compile_notes_task.output.raw,
        "strategic_notes": note_generation_task.output,
        "mom_draft_result": task_draft_email.output.raw,
        "final_crew_result": crew_result
    }
    
    return results

