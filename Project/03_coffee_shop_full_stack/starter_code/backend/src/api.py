import os
from flask import Flask, request, jsonify, abort, Response
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

"""
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
"""
#db_drop_and_create_all()


# ROUTES
@app.route("/drinks")
def get_drinks():
    get_drinks = Drink.query.order_by(Drink.id).all()
    if len(get_drinks) == 0:
        abort(404)

    drinks = [d.short() for d in get_drinks]

    return (
        jsonify(
            {
                "success": True,
                "drinks": drinks,
            }
        ),
        200,
    )


@app.route("/drinks-detail")
@requires_auth("get:drinks-detail")
def get_drinks_detail(payload):
    try:
        drinks = Drink.query.order_by(Drink.id).all()
        if len(drinks) == 0:
            abort(404)

        drinks_detail = [d.long() for d in drinks]

        return (
            jsonify(
                {
                    "success": True,
                    "drinks": drinks_detail,
                }
            ),
            200,
        )
    except Exception as e:
        print(e)
        abort(422)


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def create_drinks(payload):
    try:
        body = request.get_json()

        new_title = body.get("title", None)
        new_recipe = json.dumps(body.get("recipe", None))

        new_drink = Drink(
            title=new_title,
            recipe=new_recipe,
        )

        new_drink.insert()

        get_drinks = Drink.query.order_by(Drink.id).all()
        drinks = [d.long() for d in get_drinks]

        return (
            jsonify(
                {
                    "success": True,
                    "drinks": drinks,
                }
            ),
            200,
        )
    except BaseException:
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(payload, drink_id):
    try:
        print(drink_id)
        # Get drink to be modified
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)

        print(f"drink: {drink}")
        body = request.get_json()

        title = body.get("title", None)
        recipe = body.get("recipe", None)

        if title:
            drink.title = title

        if recipe:
            drink.recipe = json.dumps(body["recipe"])

        drink.update()

        get_drinks = Drink.query.all()
        drinks = [d.long() for d in get_drinks]

        return jsonify({"success": True, "drinks": drinks}), 200

    except BaseException:
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(payload, drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
            abort(404)

        drink.delete()

        return jsonify({"success": True, "deleted": drink_id}), 200
    except BaseException:
        abort(422)


# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify(
        {"success": False,
         "error": 422,
         "message": "unprocessable"}), 422


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False,
                 "error": 404,
                 "message": "resource not found"}),
        404,
    )


@app.errorhandler(AuthError)
def handle_auth_error(ex: AuthError) -> Response:
    """
    serializes the given AuthError as json and sets
    the response status code accordingly.
    :param ex: an auth error
    :return: json serialized ex response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
