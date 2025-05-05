from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "meow"

candidates_file = "candidates.json"
votes_file = "votes.json"
CONTACT_FILE = 'contact_submissions.json'

# Ensure contact submissions file exists
if not os.path.exists(CONTACT_FILE):
    with open(CONTACT_FILE, 'w') as f:
        json.dump([], f)

def load_candidates():
    """Helper function to load candidates from the candidates.json file."""
    if not os.path.exists(candidates_file):
        return []
    with open(candidates_file, 'r') as f:
        return json.load(f)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        contact_data = {
            'name': request.form['name'],
            'email': request.form['email'],
            'message': request.form['message'],
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(CONTACT_FILE, 'r') as f:
            submissions = json.load(f)
        submissions.append(contact_data)
        with open(CONTACT_FILE, 'w') as f:
            json.dump(submissions, f, indent=4)
        return jsonify({'message': 'Thank you! We have received your message.'}), 200
    return render_template('contact.html')

@app.route('/')
def get_started():
    return render_template('getstartedwebpage.html')

@app.route('/home')
def homepage():
    return render_template('HOMEPAGE.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('loginpage2.html')

@app.route('/process_login', methods=['POST'])
def process_login():
    voter_id = request.form['voter_id']
    password = request.form['password']
    
    with open('data/voter_data.json', 'r') as f:
        voter_data = json.load(f)
    
    # Loop through the list to find the voter with the correct ID and password
    voter = next((v for v in voter_data['voters'] if v['id'] == int(voter_id)), None)
    
    if voter and voter['password'] == password:
        session['voter_id'] = voter_id
        return redirect(url_for('vote'))
    else:
        return render_template('loginpage2.html', error="Invalid ID or password")

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    candidates = load_candidates()
    if request.method == 'POST':
        selected_id = request.form.get('selected_candidate')
        selected = next((c for c in candidates if str(c['id']) == selected_id), None)
        return render_template("confirmvote.html", candidate=selected)
    return render_template("votingpage.html", candidates=candidates)

@app.route('/add-candidate', methods=['GET', 'POST'])
def add_candidate():
    if request.method == 'POST':
        # Get the form data
        name = request.form['name']
        photo = request.files['photo']
        logo = request.files['logo']
        
        # Save the photo and logo images
        photo_filename = os.path.join('static', 'images', photo.filename)
        logo_filename = os.path.join('static', 'images', logo.filename)
        
        # Save files to disk
        photo.save(photo_filename)
        logo.save(logo_filename)

        # Create a new candidate entry
        new_candidate = {
            "id": str(len(load_candidates()) + 1),  # Ensure ID is unique
            "name": name,
            "photo": photo_filename,  # Save path
            "symbol": logo_filename  # Save path
        }
        
        # Add the new candidate to the candidates file
        candidates = load_candidates()
        candidates.append(new_candidate)

        with open(candidates_file, 'w') as f:
            json.dump(candidates, f, indent=4)

        return redirect(url_for('vote'))  # Redirect to voting page after adding candidate
    
    return render_template("vtingnew.html")

@app.route('/confirm', methods=['POST'])
def confirm():
    if session.get('voted'):
        return redirect('/already_voted')
    
    selected_id = request.form.get('selected_candidate')  # Updated to match form field name
    candidates = load_candidates()
    
    selected_candidate = next((c for c in candidates if str(c['id']) == selected_id), None)

    return render_template("confirmvote.html", candidate=selected_candidate)

@app.route('/cast-vote', methods=['POST'])
def cast_vote():
    candidate_id = request.form.get('candidate_id')

    if not candidate_id:
        return jsonify({"message": "Invalid vote"}), 400

    candidates = load_candidates()
    matched_candidate = next((c for c in candidates if str(c['id']) == candidate_id), None)

    if not matched_candidate:
        return jsonify({"message": "Invalid vote"}), 400

    # Increment vote count
    matched_candidate['votes'] = matched_candidate.get('votes', 0) + 1

    with open(candidates_file, 'w') as f:
        json.dump(candidates, f, indent=4)

    session['voted'] = True
    session['voted_candidate_id'] = candidate_id  # Store the voted candidate's ID in session

    return redirect(url_for('success'))

@app.route('/success')
def success():
    candidate_id = session.get('voted_candidate_id')
    if not candidate_id:
        return render_template('votesuccess.html', candidate=None)

    candidates = load_candidates()
    voted_candidate = next((c for c in candidates if str(c['id']) == candidate_id), None)
    return render_template('votesuccess.html', candidate=voted_candidate)

@app.route('/logout')
def logout():
    session.clear()
    return render_template('logoutpage.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/get-votes', methods=['GET'])
def get_votes():
    candidates = load_candidates()
    # Convert list of candidates to a dictionary with the candidate name as key and vote count as value
    vote_counts = {candidate['name']: candidate['votes'] for candidate in candidates}

    return jsonify(vote_counts), 200

@app.route('/get-candidates', methods=['GET'])
def get_candidates():
    candidates = load_candidates()
    return jsonify(candidates), 200

@app.route('/save-candidates', methods=['POST'])
def save_candidates():
    candidates = request.get_json()
    existing_candidates = load_candidates()

    # Save candidates as Base64 data or convert and save images if necessary
    for candidate in candidates:
        new_candidate = {
            "name": candidate["name"],
            "photo": candidate["photo"],  # Base64 data
            "symbol": candidate["symbol"]  # Base64 data
        }
        existing_candidates.append(new_candidate)
    
    with open(candidates_file, 'w') as f:
        json.dump(existing_candidates, f, indent=4)

    return jsonify({"message": "Candidates saved successfully!"}), 200

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
