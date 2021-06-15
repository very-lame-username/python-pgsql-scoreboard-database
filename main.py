# POST COMMAND: insert provided data after checking type (str, int)
# GET COMMAND: retrieve max x (default 25) results

from flask import Flask
from flask_restful import Resource, Api, reqparse
import psycopg2
import json
import os
from psycopg2.extras import RealDictCursor
import ast


# Connect to db with url
conn = psycopg2.connect(os.environ['DATABASE_URL'])


def db_get(limit):
    data = []
    # Open a cursor to perform database operations
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Query the database and obtain data as Python objects
        cur.execute("SELECT username, score FROM scoreboard ORDER BY score DESC, id ASC LIMIT %s", (limit,))
        data = json.dumps(cur.fetchall(), indent=2)
    except psycopg2.Error as e:
        conn.rollback()
        print(e)
    else:
        conn.commit()
    cur.close()
    return data


def db_post(score, user):
    # Open a cursor to perform database operations
    cur = conn.cursor()

    # Insert values
    try:
        cur.execute("INSERT INTO scoreboard (username, score) VALUES (%s, %s)",
                    (user, score))
    except psycopg2.Error as e:
        conn.rollback()
        print(e)
    else:
        conn.commit()
    cur.close()
    return


def db_delete():
    # Open a cursor to perform database operations
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM scoreboard")  # deletes entire database
    except psycopg2.Error as e:
        conn.rollback()
        print(e)
    else:
        conn.commit()
    cur.close()
    return


# Flask stuff
app = Flask(__name__)
api = Api(app)


class Scoreboard(Resource):
    def get(self):
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('limit', type=int, required=False)  # add args
        args = parser.parse_args()  # parse arguments to dictionary
        if not args['limit']:
            limit = 25
        elif args['limit'] > 9999:
            limit = 9999
        else:
            limit = args['limit']
        data = db_get(limit)
        data = ast.literal_eval(data)
        return data, 200  # return data and 200 OK code

    def post(self):
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('user', required=True)  # add args
        parser.add_argument('score', type=int, required=True)
        args = parser.parse_args()  # parse arguments to dictionary
        if len(args['user']) > 255:
            return {'message': 'User must be less than or equal to 255 characters'}, 400  # return message and 400 Bad Request code
        elif not -2147483648 <= args['score'] <= 2147483647:
            return {'message': 'Score must not exceed the range of a 4 byte int'}, 400  # return message and 400 Bad Request code
        elif not args['user']:
            return {'message': 'User may not be empty'}, 400  # return message and 400 Bad Request code

        db_post(args['score'], args['user'])
        return 'Created', 201


    def delete(self):
        parser = reqparse.RequestParser()  # initialize
        parser.add_argument('password', required=True)  # add args
        args = parser.parse_args()  # parse arguments to dictionary
        if args['password'] != 'deleteMyDatabase123$':  # insecure but it doesn't matter
            return {'message': 'Forbidden'}, 403  # return message and 403 Forbidden code
        db_delete()
        return 'Deleted', 200


api.add_resource(Scoreboard, '/scoreboard')  # '/scoreboard' is our entry point


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
