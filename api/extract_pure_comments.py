def extract_comments(payload):
    """
    Recursively extracts all comments from a nested JSON payload.

    Args:
        payload (dict): The JSON payload containing Reddit post data.

    Returns:
        list: A flat list of comment strings.
    """
    comments_list = []

    def recurse_comments(comments):
        for comment in comments:
            # Add the current comment's body to the list
            comments_list.append(comment.get("body", ""))
            # If there are replies, recurse into them
            if "replies" in comment and isinstance(comment["replies"], list):
                recurse_comments(comment["replies"])

    # Start recursion with the top-level comments
    if "data" in payload and "comments" in payload["data"]:
        recurse_comments(payload["data"]["comments"])

    return comments_list


# Example usage
if __name__ == "__main__":
    import json

    # Load the example payload from response.json
    with open("../response.json", "r", encoding="utf-8") as file:
        reddit_payload = json.load(file)

    # Extract comments
    comments = extract_comments(reddit_payload)
    print("Extracted Comments:")
    for comment in comments:
        print(comment)