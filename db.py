from functions import *
import logging
import psycopg
from psycopg import Error as PsycopgError

# Configure logging for better error tracking
logger = logging.getLogger(__name__)

def get_name_with_optional(conn, gender: str = None, country_id: str = None, age_group: str = None, min_age: int = None,
                           max_age: int = None, min_gender_probability: int = None, min_country_probability: int = None,
                           sort_by: str = None, order: str = None, page: int = 1, limit: int = 10):
    equal_to = {
        'gender': gender,
        'country_id': country_id,
        'age_group': age_group,
    }
    greater_than = {
        'max_age': max_age,
    }

    less_than = {
        'min_age': min_age,
        'min_gender_probability': min_gender_probability,
        'min_country_probability': min_country_probability
    }

    try:
        # Validate numeric parameters
        if min_age is not None and not isinstance(min_age, int):
            logger.error(f"Invalid type for min_age: {type(min_age)}")
            raise ValueError("min_age must be an integer")
        if max_age is not None and not isinstance(max_age, int):
            logger.error(f"Invalid type for max_age: {type(max_age)}")
            raise ValueError("max_age must be an integer")
        if min_gender_probability is not None and not isinstance(min_gender_probability, int):
            logger.error(f"Invalid type for min_gender_probability: {type(min_gender_probability)}")
            raise ValueError("min_gender_probability must be an integer")
        if min_country_probability is not None and not isinstance(min_country_probability, int):
            logger.error(f"Invalid type for min_country_probability: {type(min_country_probability)}")
            raise ValueError("min_country_probability must be an integer")
        if not isinstance(page, int) or page < 1:
            logger.error(f"Invalid page value: {page}")
            raise ValueError("page must be a positive integer")
        if not isinstance(limit, int) or limit < 1:
            logger.error(f"Invalid limit value: {limit}")
            raise ValueError("limit must be a positive integer")
        
        conditions = []
        valid_args_1 = {k: v for k, v in equal_to.items() if v is not None}
        valid_args_2 = {k: v for k, v in greater_than.items() if v is not None}
        valid_args_3 = {k: v for k, v in less_than.items() if v is not None}

        query = '''
            SELECT id, name, gender, gender_probability, age,
                   age_group, country_id, country_name, country_probability, created_at
            FROM name_data_table
        '''

        # Initialize the total_query here
        total_query = 'SELECT COUNT(*) FROM name_data_table'

        if valid_args_1:
            conditions.extend([f"{key} = %({key})s" for key in valid_args_1.keys()])
        if valid_args_2:
            conditions.extend([f"{str(key).replace('max_', '')} <= %({key})s" for key in valid_args_2.keys()])
        if valid_args_3:
            conditions.extend([f"{str(key).replace('min_', '')} >= %({key})s" for key in valid_args_3.keys()])

        if valid_args_1 or valid_args_2 or valid_args_3:
            where_clause = " AND ".join(conditions)
            query += f" WHERE {where_clause}"
            # Apply the exact same WHERE clause to the total count
            total_query += f" WHERE {where_clause}"

        # Fixed ORDER BY logic
        if sort_by:
            if order:
                query += f" ORDER BY {sort_by} {order}"
            else:
                query += f" ORDER BY {sort_by} ASC"

        if limit:
            query += f" LIMIT {limit}"
        if page:
            query += f" OFFSET {(page - 1) * limit}"

        valid_args = valid_args_1 | valid_args_2 | valid_args_3
        logger.info(f"Executing query with filters: {valid_args_1}")

        with conn.cursor() as cur:
            # Execute the COUNT query first
            cur.execute(total_query, valid_args)
            total = cur.fetchone()[0]

            # Execute the main data query
            cur.execute(query, valid_args)
            response_data = cur.fetchall()

        response = {
            'page': page,
            'limit': limit,
            'total': total,
            'data': arrange_response(response_data)
        }

        return response

    except ValueError as ve:
        logger.error(f"Validation error in get_name_with_optional: {ve}")
        raise
    except PsycopgError as e:
        logger.error(f"Error retrieving profiles with filters {equal_to}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_name_with_optional: {e}")
        raise

