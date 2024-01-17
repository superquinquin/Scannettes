function isAdmin() {
    let admin = false;
    if (location.pathname.split('/')[1] === "admin") {
        admin = true
    }
    return admin;
}

function unwrap_or_else(payload, errMsg) {
    if (payload.state == "err") {
        new MsgFactory("err", errMsg);
        return null;
    } else {
        return payload.data;
    }
}
