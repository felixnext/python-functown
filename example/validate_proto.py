import requests
from TestProtobufSerialization import example_pb2 as pb2
import fire


def main(app: str, key: str):
    # Create a protobuf message
    item = pb2.InformationList()
    info = item.infos.add()
    info.msg = "Hello World"
    info.id = 1
    info.score = 0.5
    for i in range(3):
        d = info.data.add()
        d.msg = f"Hello World {i}"
        d.type = pb2.Information.Importance.HIGH

    # send request to the server
    handler = "TestProtobufSerialization"
    url = f"https://{app}.azurewebsites.net/api/{handler}?code={key}"
    print(url)
    body = item.SerializeToString()
    print(body)

    response = requests.post(
        url, data=body, headers={"Content-Type": "application/octet-stream"}
    )
    print(response.status_code)

    # decode the response
    resp_item = pb2.InformationList.FromString(response.content)

    # print the response
    print(resp_item)


if __name__ == "__main__":
    fire.Fire(main)
