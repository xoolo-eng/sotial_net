from controller import Controller


Controller.include("/api/v1/user", "snet.web.user.api_urls")
Controller.include("/user", "snet.web.user.urls")
Controller.include("/chat", "snet.web.chat.urls")
