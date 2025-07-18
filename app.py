from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import json
import os
from datetime import datetime
import random
import google.generativeai as genai
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'soloquiz_secret_key_2024'

# Configure Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY', 'your-gemini-api-key-here'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Database initialization
def init_db():
    """Initialize database and create tables"""
    conn = sqlite3.connect('soloquiz.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            level TEXT NOT NULL,
            level_order INTEGER NOT NULL,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            explanation TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            selected_option TEXT,
            is_correct BOOLEAN NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def seed_database():
    """Seed database with sample questions"""
    conn = sqlite3.connect('soloquiz.db')
    cursor = conn.cursor()
    
    # Check if questions already exist
    cursor.execute('SELECT COUNT(*) FROM questions')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Sample questions for Knowledge Graphs
    sample_questions = [
        # Basics of Knowledge Graphs
        {
            'topic': 'Basics of Knowledge Graphs',
            'level': 'Pre-structural',
            'level_order': 1,
            'question': 'Which statement about Knowledge Graphs is a common misconception?',
            'options': json.dumps([
                "Knowledge Graphs are just fancy databases",
                "Knowledge Graphs represent structured knowledge using entities and relationships",
                "Knowledge Graphs enable semantic reasoning",
                "Knowledge Graphs support flexible schemas"
            ]),
            'correct_option': "Knowledge Graphs are just fancy databases",
            'explanation': 'This is a misconception. While KGs use databases for storage, they are fundamentally different - they represent semantic relationships, enable reasoning, and have flexible schemas unlike traditional databases.'
        },
        {
            'topic': 'Basics of Knowledge Graphs',
            'level': 'Uni-structural',
            'level_order': 2,
            'question': 'What is a Knowledge Graph?',
            'options': json.dumps([
                "A type of database",
                "A structured representation of knowledge using entities and relationships",
                "A search algorithm",
                "A programming language"
            ]),
            'correct_option': "A structured representation of knowledge using entities and relationships",
            'explanation': 'A Knowledge Graph is a structured way to represent real-world knowledge using entities (nodes) and their relationships (edges).'
        },
        {
            'topic': 'Basics of Knowledge Graphs',
            'level': 'Multi-structural',
            'level_order': 3,
            'question': 'Which of the following are components of a Knowledge Graph?',
            'options': json.dumps([
                "Entities and Relations",
                "Nodes and Edges",
                "Triples",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'Knowledge Graphs consist of entities (nodes), relations (edges), and are often represented as triples (subject-predicate-object).'
        },
        {
            'topic': 'Basics of Knowledge Graphs',
            'level': 'Relational',
            'level_order': 4,
            'question': 'How does a Knowledge Graph differ from a traditional relational database?',
            'options': json.dumps([
                "KGs use flexible schema",
                "KGs represent relationships explicitly",
                "KGs support semantic queries",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'Knowledge Graphs offer flexible schemas, explicit relationship representation, and semantic querying capabilities unlike rigid relational databases.'
        },
        {
            'topic': 'Basics of Knowledge Graphs',
            'level': 'Extended Abstract',
            'level_order': 5,
            'question': 'Design a Knowledge Graph solution for a smart city traffic management system. What would be the key entities and relationships?',
            'options': json.dumps([
                "Traffic lights, roads, vehicles with timing relationships",
                "Only vehicle location data",
                "Just traffic signal data",
                "Citizens, traffic lights, roads, vehicles, weather, events with complex interdependencies"
            ]),
            'correct_option': "Citizens, traffic lights, roads, vehicles, weather, events with complex interdependencies",
            'explanation': 'A comprehensive smart city KG would integrate multiple data sources and their complex relationships to enable intelligent traffic optimization and city planning.'
        },
        
        # Triples, RDF & Ontologies
        {
            'topic': 'Triples, RDF & Ontologies',
            'level': 'Uni-structural',
            'level_order': 2,
            'question': 'What does RDF stand for?',
            'options': json.dumps([
                "Resource Description Framework",
                "Relational Data Format",
                "Rapid Development Framework",
                "Remote Data Fetch"
            ]),
            'correct_option': "Resource Description Framework",
            'explanation': 'RDF (Resource Description Framework) is a standard for describing resources and their relationships in a machine-readable format.'
        },
        {
            'topic': 'Triples, RDF & Ontologies',
            'level': 'Multi-structural',
            'level_order': 3,
            'question': 'What are the three components of an RDF triple?',
            'options': json.dumps([
                "Subject, Predicate, Object",
                "Entity, Property, Value",
                "Node, Edge, Node",
                "All refer to the same concept"
            ]),
            'correct_option': "All refer to the same concept",
            'explanation': 'RDF triples consist of Subject-Predicate-Object, which can also be called Entity-Property-Value or Node-Edge-Node.'
        },
        {
            'topic': 'Triples, RDF & Ontologies',
            'level': 'Relational',
            'level_order': 4,
            'question': 'How do ontologies enhance Knowledge Graphs?',
            'options': json.dumps([
                "They provide vocabulary",
                "They define relationships",
                "They enable reasoning",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'Ontologies provide structured vocabulary, define valid relationships, and enable automated reasoning over Knowledge Graphs.'
        },
        
        # SPARQL Queries
        {
            'topic': 'SPARQL Queries',
            'level': 'Uni-structural',
            'level_order': 2,
            'question': 'What is SPARQL used for?',
            'options': json.dumps([
                "Querying RDF data",
                "Creating databases",
                "Web scraping",
                "Image processing"
            ]),
            'correct_option': "Querying RDF data",
            'explanation': 'SPARQL is a query language specifically designed for querying RDF data and Knowledge Graphs.'
        },
        {
            'topic': 'SPARQL Queries',
            'level': 'Multi-structural',
            'level_order': 3,
            'question': 'Which SPARQL keywords are used for basic queries?',
            'options': json.dumps([
                "SELECT, WHERE",
                "FROM, ORDER BY",
                "FILTER, OPTIONAL",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'SPARQL uses SELECT and WHERE for basic queries, FROM for specifying data sources, ORDER BY for sorting, and FILTER/OPTIONAL for advanced querying.'
        },
        {
            'topic': 'SPARQL Queries',
            'level': 'Relational',
            'level_order': 4,
            'question': 'How does SPARQL querying compare to SQL?',
            'options': json.dumps([
                "SPARQL works with graph patterns",
                "SQL works with tables",
                "SPARQL supports semantic matching",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'SPARQL queries graph patterns and supports semantic matching, while SQL queries structured tables with fixed schemas.'
        },
        
        # Applications of KG
        {
            'topic': 'Applications of KG',
            'level': 'Extended Abstract',
            'level_order': 5,
            'question': 'Design a Knowledge Graph application for preserving Nepali cultural heritage. What would be the key components?',
            'options': json.dumps([
                "Festival ontology with regional variations",
                "Historical timeline with cultural events",
                "Artifact catalog with provenance",
                "All integrated with multilingual support"
            ]),
            'correct_option': "All integrated with multilingual support",
            'explanation': 'A comprehensive cultural heritage KG would integrate festivals, history, artifacts, and multilingual support to preserve and share Nepali culture effectively.'
        },
        
        # Building a KG: Tools & Standards
        {
            'topic': 'Building a KG: Tools & Standards',
            'level': 'Uni-structural',
            'level_order': 2,
            'question': 'Which tool is commonly used for building Knowledge Graphs?',
            'options': json.dumps([
                "Neo4j",
                "Apache Jena",
                "Protégé",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'Neo4j (graph database), Apache Jena (RDF framework), and Protégé (ontology editor) are all popular tools for building Knowledge Graphs.'
        },
        {
            'topic': 'Building a KG: Tools & Standards',
            'level': 'Multi-structural',
            'level_order': 3,
            'question': 'What standards are important for Knowledge Graph interoperability?',
            'options': json.dumps([
                "RDF, RDFS, OWL",
                "SPARQL, JSON-LD",
                "Schema.org vocabulary",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'Interoperability requires standards like RDF/RDFS/OWL for data modeling, SPARQL for querying, JSON-LD for web integration, and Schema.org for common vocabulary.'
        },
        
        # Reasoning & Inference
        {
            'topic': 'Reasoning & Inference in KG',
            'level': 'Relational',
            'level_order': 4,
            'question': 'How does reasoning enhance Knowledge Graphs?',
            'options': json.dumps([
                "Derives new facts",
                "Validates consistency",
                "Enables intelligent queries",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'Reasoning engines can derive new facts from existing ones, validate data consistency, and enable more intelligent querying capabilities.'
        },
        
        # KGs in LLM Prompt Engineering
        {
            'topic': 'KGs in LLM Prompt Engineering',
            'level': 'Extended Abstract',
            'level_order': 5,
            'question': 'How can Knowledge Graphs improve LLM prompt engineering?',
            'options': json.dumps([
                "Provide structured context",
                "Enable fact verification",
                "Support multi-hop reasoning",
                "All of the above"
            ]),
            'correct_option': "All of the above",
            'explanation': 'Knowledge Graphs can provide structured context, enable fact verification, and support complex multi-hop reasoning to enhance LLM performance and reliability.'
        }
    ]
    
    # Insert sample questions
    for q in sample_questions:
        cursor.execute('''
            INSERT INTO questions (topic, level, level_order, question, options, correct_option, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (q['topic'], q['level'], q['level_order'], q['question'], q['options'], q['correct_option'], q['explanation']))
    
    conn.commit()
    conn.close()
    print("Database seeded with sample questions!")

def get_db_connection():
    conn = sqlite3.connect('soloquiz.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database and seed on startup
if not os.path.exists('soloquiz.db'):
    init_db()
    seed_database()

@app.template_filter('from_json')
def from_json_filter(value):
    return json.loads(value)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/start_quiz')
def start_quiz():
    # Reset session for new quiz
    session['current_question_index'] = 0
    session['score'] = 0
    session['answers'] = []
    session['username'] = request.args.get('username', 'Anonymous')
    session['ai_insights'] = []
    
    return redirect(url_for('quiz'))

@app.route('/quiz')
def quiz():
    if 'current_question_index' not in session:
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions ORDER BY level_order, id').fetchall()
    conn.close()
    
    if session['current_question_index'] >= len(questions):
        return redirect(url_for('results'))
    
    current_question = questions[session['current_question_index']]
    total_questions = len(questions)
    
    return render_template('quiz.html', 
                         question=current_question,
                         current_index=session['current_question_index'],
                         total_questions=total_questions)

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'current_question_index' not in session:
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions ORDER BY level_order, id').fetchall()
    current_question = questions[session['current_question_index']]
    
    selected_option = request.form.get('answer')
    is_correct = selected_option == current_question['correct_option']
    
    if is_correct:
        session['score'] += 1
    
    # Store answer
    answer_data = {
        'question_id': current_question['id'],
        'selected_option': selected_option,
        'is_correct': is_correct,
        'level': current_question['level'],
        'topic': current_question['topic'],
        'question_text': current_question['question']
    }
    session['answers'].append(answer_data)
    
    # Generate AI feedback using Gemini
    ai_feedback = generate_ai_feedback(current_question, selected_option, is_correct)
    
    # Save to database
    conn.execute('''INSERT INTO attempts 
                    (username, question_id, selected_option, is_correct) 
                    VALUES (?, ?, ?, ?)''',
                 (session['username'], current_question['id'], selected_option, is_correct))
    conn.commit()
    conn.close()
    
    session['current_question_index'] += 1
    
    return jsonify({
        'is_correct': is_correct,
        'explanation': current_question['explanation'],
        'ai_feedback': ai_feedback,
        'next_url': url_for('quiz') if session['current_question_index'] < len(questions) else url_for('results')
    })

@app.route('/get_ai_hint', methods=['POST'])
def get_ai_hint():
    """Get AI hint for current question"""
    data = request.get_json()
    question_text = data.get('question')
    level = data.get('level')
    topic = data.get('topic')
    
    hint = generate_ai_hint(question_text, level, topic)
    return jsonify({'hint': hint})

@app.route('/results')
def results():
    if 'score' not in session:
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions ORDER BY level_order, id').fetchall()
    conn.close()
    
    total_questions = len(questions)
    score = session['score']
    percentage = (score / total_questions) * 100
    
    # Calculate SOLO level performance
    solo_performance = calculate_solo_performance(session['answers'])
    
    # Generate comprehensive AI analysis
    ai_analysis = generate_comprehensive_ai_analysis(session['answers'], solo_performance)
    
    return render_template('results.html',
                         score=score,
                         total_questions=total_questions,
                         percentage=percentage,
                         solo_performance=solo_performance,
                         ai_analysis=ai_analysis)

@app.route('/progress')
def progress():
    conn = get_db_connection()
    
    # Get user's attempt history
    attempts = conn.execute('''
        SELECT a.*, q.level, q.topic 
        FROM attempts a 
        JOIN questions q ON a.question_id = q.id 
        ORDER BY a.timestamp DESC
    ''').fetchall()
    
    conn.close()
    
    # Calculate progress metrics
    progress_data = calculate_progress_metrics(attempts)
    
    return render_template('progress.html', progress_data=progress_data)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions ORDER BY topic, level_order').fetchall()
    conn.close()
    
    return render_template('admin.html', questions=questions)

@app.route('/add_question', methods=['POST'])
def add_question():
    topic = request.form['topic']
    level = request.form['level']
    question = request.form['question']
    options = json.dumps([
        request.form['option1'],
        request.form['option2'],
        request.form['option3'],
        request.form['option4']
    ])
    correct_option = request.form['correct_option']
    explanation = request.form['explanation']
    
    # Map SOLO levels to order
    level_order_map = {
        'Pre-structural': 1,
        'Uni-structural': 2,
        'Multi-structural': 3,
        'Relational': 4,
        'Extended Abstract': 5
    }
    
    conn = get_db_connection()
    conn.execute('''INSERT INTO questions 
                    (topic, level, level_order, question, options, correct_option, explanation) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (topic, level, level_order_map[level], question, options, correct_option, explanation))
    conn.commit()
    conn.close()
    
    flash('Question added successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/generate_question', methods=['POST'])
def generate_question():
    """Generate a new question using Gemini AI"""
    data = request.get_json()
    topic = data.get('topic')
    level = data.get('level')
    
    generated_question = generate_ai_question(topic, level)
    return jsonify(generated_question)

# AI Helper Functions using Gemini 2.0 Flash
def generate_ai_hint(question_text, level, topic):
    """Generate a helpful hint using Gemini"""
    try:
        prompt = f"""
        As an expert Knowledge Graph educator, provide a subtle hint for this SOLO {level} level question about {topic}:
        
        Question: {question_text}
        
        Provide a brief, encouraging hint that guides thinking without giving away the answer. Keep it under 50 words and make it engaging.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Think about the fundamental concepts we've covered in this topic. Consider the relationships between different elements."

def generate_ai_feedback(question, selected_option, is_correct):
    """Generate personalized AI feedback using Gemini"""
    try:
        options = json.loads(question['options'])
        correct_option = question['correct_option']
        
        prompt = f"""
        As a Knowledge Graph learning expert, provide personalized feedback for this student response:
        
        Question: {question['question']}
        SOLO Level: {question['level']}
        Topic: {question['topic']}
        Options: {', '.join(options)}
        Student Selected: {selected_option}
        Correct Answer: {correct_option}
        Result: {'Correct' if is_correct else 'Incorrect'}
        
        Provide encouraging, specific feedback that:
        1. Acknowledges their thinking process
        2. Explains why the answer is correct/incorrect
        3. Connects to SOLO taxonomy level
        4. Suggests next learning steps
        
        Keep it conversational and under 100 words.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Great effort! Keep building your understanding of Knowledge Graphs step by step."

def generate_comprehensive_ai_analysis(answers, solo_performance):
    """Generate comprehensive learning analysis using Gemini"""
    try:
        # Prepare performance summary
        performance_summary = []
        for level, perf in solo_performance.items():
            if perf['total'] > 0:
                performance_summary.append(f"{level}: {perf['correct']}/{perf['total']} ({perf['percentage']:.0f}%)")
        
        prompt = f"""
        As an expert educational psychologist specializing in SOLO Taxonomy and Knowledge Graphs, analyze this student's learning journey:
        
        Performance Summary:
        {chr(10).join(performance_summary)}
        
        Total Questions: {len(answers)}
        
        Provide a comprehensive analysis including:
        1. SOLO taxonomy progression insights
        2. Knowledge Graph concept mastery
        3. Learning strengths and growth areas
        4. Specific recommendations for advancement
        5. Motivational encouragement
        
        Structure as: **Strengths** | **Growth Areas** | **Next Steps** | **Encouragement**
        Keep each section concise but meaningful.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "You're making excellent progress in your Knowledge Graph learning journey! Keep exploring and connecting concepts across different levels."

def generate_ai_question(topic, level):
    """Generate a new question using Gemini AI"""
    try:
        prompt = f"""
        Create a {level} level Knowledge Graph question about {topic} following SOLO Taxonomy principles:
        
        SOLO Level Guidelines:
        - Pre-structural: Test misconceptions
        - Uni-structural: Single concept focus
        - Multi-structural: Multiple related concepts
        - Relational: Connections between concepts
        - Extended Abstract: Real-world applications
        
        Return a JSON object with:
        {{
            "question": "Question text",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_option": "Exact text of correct option",
            "explanation": "Detailed explanation"
        }}
        
        Ensure the question is educationally sound and appropriate for the SOLO level.
        """
        
        response = model.generate_content(prompt)
        # Parse the JSON response
        import re
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"error": "Could not generate question"}
    except Exception as e:
        return {"error": f"Error generating question: {str(e)}"}

def calculate_solo_performance(answers):
    """Calculate performance across SOLO levels"""
    solo_levels = ['Pre-structural', 'Uni-structural', 'Multi-structural', 'Relational', 'Extended Abstract']
    performance = {}
    
    for level in solo_levels:
        level_answers = [a for a in answers if a['level'] == level]
        if level_answers:
            correct = sum(1 for a in level_answers if a['is_correct'])
            performance[level] = {
                'correct': correct,
                'total': len(level_answers),
                'percentage': (correct / len(level_answers)) * 100
            }
        else:
            performance[level] = {'correct': 0, 'total': 0, 'percentage': 0}
    
    return performance

def calculate_progress_metrics(attempts):
    """Calculate detailed progress metrics"""
    if not attempts:
        return {}
    
    # Group by topic and level
    topic_performance = {}
    level_performance = {}
    
    for attempt in attempts:
        topic = attempt['topic']
        level = attempt['level']
        
        if topic not in topic_performance:
            topic_performance[topic] = {'correct': 0, 'total': 0}
        if level not in level_performance:
            level_performance[level] = {'correct': 0, 'total': 0}
        
        topic_performance[topic]['total'] += 1
        level_performance[level]['total'] += 1
        
        if attempt['is_correct']:
            topic_performance[topic]['correct'] += 1
            level_performance[level]['correct'] += 1
    
    # Calculate percentages
    for topic in topic_performance:
        total = topic_performance[topic]['total']
        if total > 0:
            topic_performance[topic]['percentage'] = (topic_performance[topic]['correct'] / total) * 100
    
    for level in level_performance:
        total = level_performance[level]['total']
        if total > 0:
            level_performance[level]['percentage'] = (level_performance[level]['correct'] / total) * 100
    
    return {
        'topic_performance': topic_performance,
        'level_performance': level_performance,
        'total_attempts': len(attempts)
    }

if __name__ == '__main__':
    app.run(debug=True)