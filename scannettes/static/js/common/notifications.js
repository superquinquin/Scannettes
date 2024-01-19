
class MsgFactory {
    constructor(containerId, mtype, msg, fade=false, sleep=0, speed=0) {
        const container = document.getElementById(containerId);

        let frame = this.buildFrame(mtype);
        frame.appendChild(this.buildSymbol(mtype));
        frame.appendChild(this.buildMsg(msg));
        frame.appendChild(this.buildExit());

        let node = container.appendChild(frame);
        if (fade) {
            this.fadeOut(node, sleep, speed);
        }
    }


    buildFrame(mtype) {
        let frame = document.createElement("div");
        frame.classList.add(mtype, "msg-container");
        frame.style.opacity = 100;
        return frame;
    }

    buildSymbol(mtype) {
        let elm = document.createElement('img');
        elm.classList.add("msg-symbol","msg-comp"); 
        elm.setAttribute("src","/static/misc/"+mtype+".png");
        return elm;
    }

    buildMsg(msg) {
        let elm = document.createElement("p");
        elm.classList.add("msg", "msg-comp");
        elm.innerHTML = msg;
        return elm;
    }

    buildExit() {
        let elm = document.createElement("div");
        elm.classList.add("quit-container");
        
        let btn = document.createElement("button");
        btn.classList.add("msg-quit", "msg-comp");
        btn.setAttribute("onclick", "closeMsg(this)");
        btn.innerText = "x";

        elm.appendChild(btn);
        return elm;   
    }

    async fadeOut(node, slp, speed) {
        await sleep(slp);
        node.style.transition = speed+'ms';
        node.style.opacity = 0;
        await sleep(speed);
        node.remove();
    }
}

function closeMsg(elm) {
    let box = elm.parentElement.parentElement;
    box.remove();
}

function sleep (time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}
