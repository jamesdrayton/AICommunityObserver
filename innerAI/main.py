from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flasgger import Swagger
import os

from testing.testing import testing_bp

app = Flask(__name__) 
swagger = Swagger(app)

@app.route('/swagger')
def swagger():
    """
    A simple index endpoint
    ---
    responses:
      200:
        description: Returns a welcome message
        examples:
          application/json: { "message": "Welcome to the API!" }
    """
    return jsonify(message="Welcome to the API!")

@app.route("/routes")
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "rule": str(rule)
        })
    return {"routes": routes}
    
app.register_blueprint(testing_bp)

if __name__ == '__main__':
    app.run(debug=True, port=8000)