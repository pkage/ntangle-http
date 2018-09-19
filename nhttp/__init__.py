import zmq
import json
import click
import msgpack
import asyncio
import zmq.asyncio
from aiohttp import web

# something happened on the remote
class RemoteError(Exception):
    pass

# client class to proxy a remote object
class NHTTPBridge:
    remote = ""
    listing = []
    __socket = None
    __context = None
    __debug = False

    # set up the object
    def __init__(self, remote, context=None, debug=False):
        self.remote = remote
        self.__debug = debug

        # if we don't have a zmq context, create a new one
        if context is None:
            self.__context = zmq.asyncio.Context.instance()
        else:
            self.__context = context

        # create a socket
        self.__socket = self.__context.socket(zmq.REQ)
        self.__socket.connect(remote)

        # connect to the remote
        #self.__refresh_remote()

    # make a remote function call
    async def call(self, req):
        # create a new socket
        sock = self.__context.socket(zmq.REQ)
        sock.connect(self.remote)

        # process function name
        func = req.path[1:].split('/')[0]

        # figure out arguments
        args = None

        # sort out the arguments to the function calls
        if req.method == 'GET':
            # extract from GET path
            if '/' in req.path[1:]:
                args = req.path[1:].split('/')[1:]
        else:
            # extract from POST body
            if req.can_read_body and req.content_type == 'application/json':
                try:
                    args = (await req.json())['args']
                except:
                    return Response(
                            text=json.dumps({
                                'success': False,
                                'return': 'client error'
                            }),
                            status_code=400,
                            content_type='application/json'
                        )

        # construct the function call
        payload = {'func': func}
        if args is not None:
            payload['args'] = args
        else:
            payload['args'] = []

        # pack the payload
        payload = msgpack.packb(payload)

        # send off
        await sock.send(payload)

        # wait back from the server
        msg = await sock.recv()
        msg = msgpack.unpackb(msg, raw=False)

        sock.close()

        if msg['success']:
            return web.Response(
                    text=json.dumps(msg),
                    content_type='application/json'
            )
        else:
            if self.__debug:
                return web.Response(
                        text=json.dumps(msg),
                        content_type='application/json',
                        status=500
                    )
            else:
                raise RemoteError(msg)

    # make this more easily debuggable
    def __repr__(self):
        return '<ntangle http bridge @ {}>'.format(self.remote)


@click.command()
@click.argument('remote')
@click.option('--port', default=8080, help='the port to serve on')
@click.option('--debug', is_flag=True)
def main(remote, port, debug):
    # debug notice
    if debug:
        print('running in debug mode')

    # create the bridge
    bridge = NHTTPBridge(remote, debug=debug)

    # create the http server
    app = web.Application()
    app.add_routes([
        web.get( '/{tail:.+}', bridge.call),
        web.post('/{tail:.+}', bridge.call)
    ])

    # launch the server
    web.run_app(app, port=port)
