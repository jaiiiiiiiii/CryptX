from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from cryptography.fernet import Fernet
import os
import zipfile
import io
import json

app = Flask(__name__)
CORS(app)

@app.route('/api/encrypt', methods=['POST'])
def encrypt_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Generate key
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        
        # Read and encrypt file
        file_data = file.read()
        encrypted_data = cipher_suite.encrypt(file_data)
        
        # Create ZIP in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Save encrypted file
            zipf.writestr('encrypted_file', encrypted_data)
            
            # Save key and original filename in metadata
            metadata = {
                'key': key.decode('utf-8'),
                'original_filename': file.filename
            }
            zipf.writestr('metadata.json', json.dumps(metadata))
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'encrypted_{file.filename}.zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/decrypt', methods=['POST'])
def decrypt_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        zip_file = request.files['file']
        if zip_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Read ZIP in memory
        zip_data = io.BytesIO(zip_file.read())
        
        with zipfile.ZipFile(zip_data, 'r') as zipf:
            # Read metadata
            metadata = json.loads(zipf.read('metadata.json'))
            key = metadata['key'].encode('utf-8')
            original_filename = metadata['original_filename']
            
            # Read encrypted data
            encrypted_data = zipf.read('encrypted_file')
        
        # Decrypt the file
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        
        # Create memory file for sending
        memory_file = io.BytesIO(decrypted_data)
        memory_file.seek(0)
        
        # Ensure the decrypted file is saved as .txt and set the MIME type to text/plain
        decrypted_filename = f'decrypted_{os.path.splitext(original_filename)[0]}.txt'
        
        return send_file(
            memory_file,
            mimetype='text/plain',  # Set MIME type to text/plain
            as_attachment=True,
            download_name=decrypted_filename  # Ensure it downloads as .txt
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)