import views


def get_controller_info(reactorno, debug=False, crio=False):
    reactor = views.Reactor.query.filter_by(idx=reactorno).first()
    ip = reactor.controller.ip
    # If debug mode, return debug port. Else, return application port.
    if debug:
        port = reactor.controller.debug_port
    else:
        port = reactor.controller.port
    # If requested crio ID return that.
    if crio:
        crio = reactor.controller.idx
        return ip, port, crio
    else:
        return ip, port