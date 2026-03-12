from __future__ import annotations


class APIError(Exception):
	"""Base application error with HTTP status and title."""

	status_code: int = 400
	title: str = "Bad Request"

	def __init__(self, message: str | None = None, *, status_code: int | None = None, title: str | None = None) -> None:
		super().__init__(message or self.title)
		if status_code is not None:
			self.status_code = status_code
		if title is not None:
			self.title = title


class AuthenticationError(APIError):
	status_code = 401
	title = "AuthenticationError"


class InvalidCredentialsError(AuthenticationError):
	title = "InvalidCredentialsError"


class UserDoesNotExist(APIError):
	status_code = 401
	title = "UserDoesNotExist"


class InvalidTokenError(AuthenticationError):
	title = "InvalidTokenError"


class TokenRevokedError(AuthenticationError):
	title = "TokenRevokedError"


class MissingRefreshTokenError(AuthenticationError):
	title = "MissingRefreshTokenError"


class InvalidRefreshTokenError(AuthenticationError):
	title = "InvalidRefreshTokenError"


class EmailVerificationError(APIError):
	title = "EmailVerificationError"


class EmailVerificationNotVerified(APIError):
	status_code = 401
	title = "EmailVerificationNotVerified"


class BookmarkAlreadyExistsError(APIError):
	title = "BookmarkAlreadyExistsError"


class BookmarkDoesNotExistError(APIError):
	title = "BookmarkDoesNotExistError"


class BookmarkAlreadyExistsError(APIError):
	title = "BookmarkAlreadyExistsError"


class BookmarkDoesNotExistError(APIError):
	title = "BookmarkDoesNotExistError"


class DuplicateInterestError(APIError):
	status_code = 409
	title = "DuplicateInterestError"


class ArticleNotFoundError(APIError):
	status_code = 404
	title = "ArticleNotFoundError"


class InvalidFieldError(APIError):
	status_code = 400
	title = "InvalidFieldError"


class ArticleWithSlugNotFound(APIError):
	title = "ArticleWithSlugNotFound"


class UserAlreadyExists(APIError):
	status_code = 409
	title = "UserAlreadyExists"


class FeedbackCreateFailedError(APIError):
	status_code = 400
	title = "FeedbackCreateFailedError"

