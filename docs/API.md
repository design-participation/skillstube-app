# API

This document describes the API of the How-To-App server.

## Search (`src/search.py`)

* `GET /`: redirect to /search
* `GET /search?q=text&prompt=num&channel_only=bool`: search youtube with a given query, the selected prompt and a boolean indicating to search the target channel. Search parameters are saved to the session token to survive navigation.
* `GET /watch/{video_id}`: watch a given video using its youtube id
* `GET /suggest?q=text&prompt=num`: get query suggestions from google for a given prompt+query

## Users (`src/users.py`)
* `GET /new-user`: show new user form
* `POST /new-user`: create user. Expects POST data: email, name, password, picture (image data). The picture is thumbailed and saved to data/pictures. If no picture was given, a surrogate is used.
* `GET /login`: show login form
* `POST /login`: login user. If a qrcode is given, the user is logged with that qrcode, otherwise, email/password are checked. A new session cookie is created to keep the user logged-in.
* `GET /logout`: logout user
* `GET /user`: show user profile
* `GET /user-modify`: show profile modification form
* `POST /user/change-picture`: upload a new picture for current user
* `POST /user/change-password`: change password of current user

## Friends (`src/friend.py`)

* `GET /friends`: show list of friend
* `POST /friend/request`: send friend request using email or add friend with qrcode 
* `GET /friend/request/{request_id}`: view friend request
* `GET /friend/accept/{request_id}`: accept friend request

## Notifications (`src/notification.py`)

* `GET /dismiss/{notification_id}`: dismiss notification (mark as read)
* `GET /notification/{notification_id}`: reroute user to page corresponding to notification according to type
* `GET /notifications`: show list of new notifications
* `GET /notifications/old`: show old notifications (already read)
* `GET /notifications/all`: show all notifications (old and new)

## Playlists (`src/playlist.py`)

* `GET /playlists`: show list of folders (playlists)
* `GET /playlists/{folder_id}`: show videos of a given playlist
* `GET /set_playlist/{video_id}`: get playlist selection form
* `POST /set_playlist/{video_id}`: change playlist for a video

## Comments (`src/comment.py`)

* `GET /comment/{video_id} `: show comment composition form
* `POST /comment/{video_id}`: create comment in db. Form data should contain a text field and multiple friend fields. The comment is shared to the list of friends.

## Sharing (`src/share.py`)

* `GET /shared`: show list of videos shared with user

Deprecated:
* `GET /shared/by-me`: show list of videos shared by user 
* `GET /shared/{friend_id}`: show list of videos shared by friend with user
* `GET /share/{comment_id}`: form for sharing a comment
* `POST /share/{comment_id}`: actually share the comment

## Logging (`src/history.py`)

* `GET /history`: show whole history of a user
* `GET /history/{category}`: show history of a given category of events for user
* `POST /action`: log client-side action. Post data contains a type and parameters encoded as json. See /static/client.js for examples. Only allowed action types are saved.

## Export (`src/export.py`)

* `GET /export`: show export password form
* `POST /export`: generate xlsx download with exported data 

## Speech recognition (`src/speech.py`)

* `GET /stt/microsoft`: get temporary speech recognition token (see /static/stt.js)

## Debug (`src/debug.py`)

Run server with `-debug` in command line.

Introspection:
* `GET /debug:users`: list all users
* `GET /debug:login/{user_id}`: login as a specific user
* `GET /debug:restart`: restart server
* `GET /debug:videos`: list all videos known in the DB
* `GET /debug:history`: whole history in json format

Dangerous:
* `GET /debug:clear`: clear the database
* `GET /debug:populate`: populate the DB with a set of users and interactions

