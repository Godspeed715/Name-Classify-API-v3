"""
Name-Classify-API-v3
Demographic Intelligence API for Profile Querying and Filtering

This module provides RESTful endpoints for querying demographic profiles
with advanced filtering, sorting, pagination, and natural language support.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg as ps
from db import *
from functions import *
from psycopg import Error as PsycopgError
import logging

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
"""Configure application-wide logging for better error tracking and debugging."""
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK APPLICATION INITIALIZATION
# ============================================================================
"""Initialize Flask app with JSON serialization and CORS support."""
app = Flask(__name__)
app.json.sort_keys = False
CORS(app)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================
"""Establish connection to PostgreSQL database."""
DB_URI = 'postgresql://postgres:1234@localhost:5432/postgres'
connection = None

try:
    connection = ps.connect(DB_URI)
    logger.info("Successfully connected to the database")
except PsycopgError as e:
    logger.error(f"Failed to connect to the database: {e}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
# (No utility functions required)

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/profiles', methods=['GET'])
def get_with_optional():
    """
    GET /api/profiles
    
    Retrieve demographic profiles with optional filtering, sorting, and pagination.
    
    Supported Query Parameters:
        - gender (str): Filter by 'male' or 'female'
        - age_group (str): Filter by age group ('child', 'teen', 'adult', 'senior', 'young')
        - country_id (str): Filter by ISO country code (e.g., 'NG', 'US')
        - min_age (int): Minimum age filter
        - max_age (int): Maximum age filter
        - min_gender_probability (int): Minimum gender confidence score
        - min_country_probability (int): Minimum country confidence score
        - sort_by (str): Sort by field ('age', 'created_at', 'gender_probability')
        - order (str): Sort order ('asc' or 'desc')
        - page (int): Page number for pagination (default: 1)
        - limit (int): Results per page (default: 10, max: 50)
    
    Returns:
        JSON response with paginated profiles and metadata
    """
    # Define allowed query parameters to prevent injection of unexpected parameters
    allowed_parameters = [
        "gender", "country_id", "age_group", "min_age", "max_age",
        "min_gender_probability", "min_country_probability",
        "sort_by", "order", "page", "limit"
    ]

    try:
        # ====================================================================
        # PARAMETER VALIDATION: Check for unknown parameters
        # ====================================================================
        """
        Validate that only known query parameters are provided.
        Reject unknown parameters to prevent potential security issues.
        """
        provided_parameters = set(request.args.to_dict().keys())
        unknown_parameters = provided_parameters - set(allowed_parameters)
        
        if unknown_parameters:
            logger.warning(f"Unknown query parameters provided: {unknown_parameters}")
            return jsonify({
                "status": "error",
                "message": f"Invalid query parameters: {', '.join(unknown_parameters)}"
            }), 422

        # ====================================================================
        # PARAMETER EXTRACTION AND TYPE CONVERSION
        # ====================================================================
        """
        Extract and validate each parameter with proper type conversion.
        Flask's request.args.get() handles type conversion automatically.
        """
        try:
            gender = request.args.get('gender', default=None, type=str)
            country_id = request.args.get('country_id', default=None, type=str)
            age_group = request.args.get('age_group', default=None, type=str)
            min_age = request.args.get('min_age', default=None, type=int)
            max_age = request.args.get('max_age', default=None, type=int)
            min_gender_probability = request.args.get('min_gender_probability', default=None, type=int)
            min_country_probability = request.args.get('min_country_probability', default=None, type=int)
            sort_by = request.args.get('sort_by', default=None, type=str)
            order = request.args.get('order', default=None, type=str)
            page = request.args.get('page', default=1, type=int)
            limit = request.args.get('limit', default=10, type=int)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid parameter type: {e}")
            return jsonify({'status': 'error', 'message': 'Invalid parameter type'}), 422

        # ====================================================================
        # PARAMETER VALIDATION: Semantic validation of values
        # ====================================================================
        """
        Validate specific parameter values against allowed sets.
        Ensures that enum-type parameters only contain valid values.
        """
        valid_age_groups = ['child', 'teen', 'adult', 'senior', 'young']
        if age_group and age_group not in valid_age_groups:
            logger.warning(f"Invalid age_group value: {age_group}")
            return jsonify({
                'status': 'error',
                'message': f'Invalid age_group. Must be one of: {", ".join(valid_age_groups)}'
            }), 422

        # ====================================================================
        # DATABASE QUERY
        # ====================================================================
        """Execute database query with validated parameters."""
        logger.info(
            f"Querying profiles - gender: {gender}, country_id: {country_id}, "
            f"age_group: {age_group}, page: {page}, limit: {limit}"
        )
        
        profiles = get_name_with_optional(
            conn=connection,
            gender=gender,
            country_id=country_id,
            age_group=age_group,
            min_age=min_age,
            max_age=max_age,
            min_gender_probability=min_gender_probability,
            min_country_probability=min_country_probability,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit
        )

        # ====================================================================
        # RESPONSE HANDLING
        # ====================================================================
        """Check results and return appropriate response."""
        if not profiles or not profiles['data']:
            logger.info("No profiles found matching the provided filters")
            return jsonify({
                'status': 'error',
                'message': 'Profile not found'
            }), 404

        logger.info(f"Successfully retrieved {len(profiles['data'])} profiles")
        return jsonify({
            'status': 'success',
            'page': profiles['page'],
            'limit': profiles['limit'],
            'total': profiles['total'],
            'data': profiles['data']
        }), 200

    except PsycopgError as db_error:
        logger.error(f"Database error in get_with_optional: {db_error}")
        return jsonify({
            'status': 'error',
            'message': 'Error retrieving profiles from database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_with_optional: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500


@app.route('/api/profiles/search', methods=['GET'])
def nlp():
    """
    GET /api/profiles/search
    
    Search profiles using natural language queries.
    
    The query string is parsed into structured filter parameters using
    a rule-based NLP system (no AI/LLM required).
    
    Query Parameters:
        - q (str, required): Natural language query string
    
    Query Examples:
        - "young males from nigeria" → gender=male, age 16-24, country=NG
        - "females above 30" → gender=female, min_age=30
        - "adult males from kenya" → gender=male, age_group=adult, country=KE
    
    Returns:
        JSON response with matching profiles and pagination metadata
    """
    try:
        # ====================================================================
        # PARAMETER EXTRACTION AND VALIDATION
        # ====================================================================
        """Extract and validate the required search query parameter."""
        q = request.args.get('q', default=None, type=str)
        
        if not q or q.strip() == '':
            logger.warning("Search query parameter 'q' is missing or empty")
            return jsonify({
                'status': 'error',
                'message': 'Query parameter "q" is required'
            }), 400
        
        # ====================================================================
        # NATURAL LANGUAGE QUERY PROCESSING
        # ====================================================================
        """
        Parse natural language query into structured filter parameters.
        Uses rule-based pattern matching with spaCy NER and custom entity rules.
        """
        logger.info(f"Processing natural language query: '{q}'")
        query_params = extract_query_params(q)
        logger.info(f"Extracted query parameters: {query_params}")
        
        # ====================================================================
        # DATABASE QUERY
        # ====================================================================
        """Execute database query with extracted parameters."""
        response = get_name_with_optional(connection, **query_params)
        
        # ====================================================================
        # RESPONSE HANDLING
        # ====================================================================
        """Check results and return appropriate response."""
        if not response or not response['data']:
            logger.info(f"No profiles found for query: '{q}'")
            return jsonify({
                'status': 'error',
                'message': 'Unable to interpret query'
            }), 400
        
        logger.info(f"Successfully processed search query and retrieved {len(response['data'])} profiles")
        return jsonify({
            'status': 'success',
            'page': response['page'],
            'limit': response['limit'],
            'total': response['total'],
            'data': response['data']
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing search query: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to interpret query'
        }), 400

# ============================================================================
# ERROR HANDLERS
# ============================================================================
"""
Global error handlers for common HTTP errors.
Ensures consistent error response format across all error scenarios.
"""

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 Not Found errors."""
    logger.warning("404 - Page not found")
    return jsonify({
        'status': 'error',
        'message': 'Page Not Found. Check your URL.'
    }), 404


@app.errorhandler(502)
def site_error(e):
    """Handle 502 Bad Gateway errors."""
    logger.error("502 - Bad Gateway error")
    return jsonify({
        'status': 'error',
        'message': 'Site is Temporarily Down.'
    }), 502


@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server errors."""
    logger.error(f"500 - Internal server error: {e}")
    return jsonify({
        'status': 'error',
        'message': 'Server Error'
    }), 500

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    """
    Main entry point for the application.
    Starts the Flask development server and ensures proper cleanup
    of database connections on shutdown.
    """
    try:
        logger.info("Starting Name-Classify-API-v3 server")
        app.run(debug=True)
    finally:
        """Ensure proper cleanup of database connection on application shutdown."""
        if connection:
            connection.close()
            logger.info("Database connection closed")

