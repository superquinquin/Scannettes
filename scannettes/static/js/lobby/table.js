function rmPlaceholder() {
    const table = document.getElementById("room-table");
    let placeholder = table.getElementsByClassName("placeholder");
    if (placeholder.length > 0) {
        placeholder[0].remove();
    }
}

function addPlaceholder() {
    const table = document.getElementById("room-table");
    let purchases = table.getElementsByClassName("purchase");
    let placeholder = table.getElementsByClassName("placeholder");
    if (purchases.length === 0 & placeholder.length === 0) {
        new RoomFactory("placeholder");
    }
}


class MenuFactory {
    constructor() {
        const container = document.getElementById("actions");
        container.appendChild(this.btnBuilder("Créer", "create", ["btn-small", "border", "side-margin"], "creationModal()"));
        container.appendChild(this.btnBuilder("Supprimer", "del", ["btn-small", "border", "side-margin"], "delSelRooms()"));
        container.appendChild(this.btnBuilder("Recharger", "reset", ["btn-small", "border", "side-margin"], "confRecharge()"));
        container.appendChild(this.btnBuilder("QR-code", "qrcode", ["btn-small", "border", "side-margin"], "GenerateQrCode()"));
    }

    btnBuilder(text, id, cls, onclick) {
        let btn = document.createElement("button");
        btn.setAttribute("id", id);
        btn.setAttribute("onclick", onclick);
        btn.classList.add(...cls);
        btn.innerText = text;
        return btn;
    }
}

class RoomFactory {
    constructor(payload) {
        const table = document.getElementById("room-table");
        if (payload === "placeholder") {
            table.appendChild(this.placeHolder())
        } else {
            let frame = this.buildRoom(payload);
            table.appendChild(frame);
        }
    }

    buildRoom(payload) {
        let frame = this.buildFrame(payload);

        frame.appendChild(this.buildCheckBox())
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildCell(this.defaultName(payload), ["grid-cell", "padding", "long", "rname"]));
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildCell(payload.display_name, ["grid-cell", "padding", "pname"]));
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildCell(this.translateState(payload.state), ["grid-cell", "padding", "long", "pstate"]));
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildCell(payload.creating_date, ["grid-cell", "padding", "long", "pdate"]));
        frame.appendChild(this.buildSeparator());
        frame.appendChild(this.buildPassCell());
        frame.appendChild(this.buildAccessBtn(payload.origin, payload.token, payload.rid));
        return frame;
    }

    buildFrame(payload) {
        let elm = document.createElement("div");
        elm.classList.add("purchase", "border", payload.state);
        elm.setAttribute("id", payload.rid);
        elm.setAttribute("state", payload.state);
        elm.setAttribute("sibling", payload.sibling);
        elm.setAttribute("otype", payload.type);
        elm.setAttribute("oid", payload.oid);
        elm.setAttribute("rid", payload.rid);
        elm.setAttribute("token", payload.token);
        return elm;
    }

    buildCheckBox() {
        let elm = document.createElement("div");
        elm.classList.add("grid-cell", "check");

        let inp = document.createElement("input");
        inp.classList.add("selectBox");
        inp.setAttribute("type","checkbox");

        elm.appendChild(inp);
        return elm;
    }

    buildCell(text, classes) {
        let elm = document.createElement("div");
        elm.innerText = text;
        for (var cls of classes) {
            elm.classList.add(cls);
        }
        return elm;
    }

    buildPassCell() {
        let elm = document.createElement("div");
        elm.classList.add("grid-cell", "rpass");

        let inp = document.createElement("input");
        inp.setAttribute("type", "password");
        inp.setAttribute("autocomplete", "off");
        inp.setAttribute("placeholder", "Mot de passe...");

        if (!rPass) {
            inp.readOnly = true;
        }
        elm.appendChild(inp);
        return elm;
    }

    buildAccessBtn(origin, token, rid) {
        if (admin) {
            origin = origin + "/admin/room";
        } else {
            origin = origin + "/room";
        }

        let url = origin+"/"+token+"?rid="+rid;
        let elm = document.createElement("div");
        elm.classList.add("grid-cell-btn", "raccess");

        let redirector = document.createElement("a");
        redirector.setAttribute("href", url)

        let btn = document.createElement("button");

        let iframe = document.createElement("i");
        iframe.classList.add("arrow", "right");

        btn.appendChild(iframe);
        redirector.appendChild(btn)
        elm.appendChild(redirector);
        return elm;
    }

    buildSeparator() {
        let elm = document.createElement("div");
        elm.classList.add("separator");
        return elm;
    }

    placeHolder() {
        let elm = document.createElement("div");
        elm.classList.add("placeholder", "border");

        let text = document.createElement("p");
        text.innerText = "Aucun Salon";

        elm.appendChild(text);
        return elm;
    }

    translateState(state) {
        if (state == "open") {
            return "Ouvert";
        } else if (state == "close") {
            return "Fermé";
        } else if (state == "done") {
            return "Archivé";
        }
    }

    defaultName(payload) {
        if (payload.name != "") {
            return payload.name;
        }
        let rid = payload.rid;
        return "Salon n° " + rid;
    }
}

