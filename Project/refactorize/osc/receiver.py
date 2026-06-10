# osc/receiver.py

def make_osc_handler(
    state,
    engine
):

    def handle_distances(
        address,
        *args
    ):

        try:

            tag_id = int(args[0])

            distances = [
                float(v)
                for v in args[1:]
            ]

            engine.update_tag(
                tag_id,
                distances
            )

        except Exception as exc:

            print(
                f"[OSC ERROR] {exc}"
            )

    return handle_distances