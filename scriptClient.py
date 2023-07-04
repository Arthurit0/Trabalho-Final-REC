import subprocess
import threading
import time
import sys
import os
import glob


def run_iperf_tcp_client(ip, port, duration, bitrate, cong_alg, json):
    command = [
        "iperf3",
        "-c",
        ip,
        "-p",
        str(port),
        "-t",
        str(duration),
        "-C",
        cong_alg,
    ]

    if bitrate != "":
        command = command + ["-b", f"{bitrate}Mb"]

    format = "txt"

    if json == "S":
        format = "json"
        command.append("-J")

    try:
        with open(f"./client_tcp_port_{port}.{format}", "w") as outfile:
            process = subprocess.Popen(command, stdout=subprocess.PIPE)

            for line in process.stdout:
                print(line.decode().strip(), file=outfile)
    except Exception as e:
        print(f"Um erro ocorreu: {e}", file=sys.stderr)


def run_iperf_udp_client(ip, port, duration, bitrate, json):
    command = [
        "iperf3",
        "-c",
        ip,
        "-p",
        str(port),
        "-u",
        "-b",
        f"{bitrate}Mb",
        "-t",
        str(duration),
    ]

    format = "txt"

    if json == "S":
        format = "json"
        command.append("-J")

    try:
        with open(f"./client_udp_port_{port}.{format}", "w") as outfile:
            process = subprocess.Popen(command, stdout=subprocess.PIPE)

            for line in process.stdout:
                print(line.decode().strip(), file=outfile)

    except Exception as e:
        print(f"Um erro ocorreu: {e}", file=sys.stderr)


def main():
    atraso = 5

    print("Para ambos os servidores:\n")

    server_ip = ''

    while server_ip == '':
        server_ip = input("Digite o IP alvo: ")
        if server_ip == '':
            print("IP inválido!", end=" ")

    duration = input(
        f"\nDigite a duração dos envios (Em segundos, Enter para 10 segundos, haverá um atraso de {atraso} segundos entre o início da conexão TCP e UDP): "
    )

    if duration == "":
        duration = 10
    else:
        duration = int(duration)

    json = False

    while json not in ["", "S", "N"]:
        json = input(
            "Formato de exportação dos arquivos em JSON? (Enter ou 'S' para JSON, 'N' para TXT): "
        )

        if json not in ["", "S", "N"]:
            print("Resposta inválida!", end=" ")

    if json == "":
        json = "S"

    print("\nPara o TCP:\n")

    num_tcp = input("Digite o número de conexões TCP (Enter para 1): ")

    if num_tcp == '' or int(num_tcp) <= 1:
        num_tcp = 1
    else:
        num_tcp = int(num_tcp)

    tcp_clients = []
    tcp_port = 5202

    if num_tcp == 1:
        cong_alg = False

        while cong_alg not in ["", "cubic", "reno"]:
            cong_alg = input(
                'Qual algoritmo de congestionamento você quer para o TCP ("cubic" ou "reno", Enter para "cubic"): '
            ).lower()

            if cong_alg not in ["", "cubic", "reno"]:
                print('\nResposta inválida! Escolha entre "cubic" ou "reno"! \n')

        if cong_alg == "":
            cong_alg = "cubic"

        tcp_bitrate = input(
            "Qual a vazão (ou bitrate) você quer para o TCP (em Mb, enter para Ilimitado): "
        )
    else:
        for i in range(num_tcp):
            print(f"\nConexão TCP {i+1}:\n")
            cong_alg = False

            while cong_alg not in ["", "cubic", "reno"]:
                cong_alg = input(
                    f'Qual algoritmo de congestionamento você quer para o TCP {i+1} ("cubic" ou "reno", Enter para "cubic"): '
                ).lower()

                if cong_alg not in ["", "cubic", "reno"]:
                    print('\nResposta inválida! Escolha entre "cubic" ou "reno"! \n')

            if cong_alg == "":
                cong_alg = "cubic"

            tcp_bitrate = input(
                f"Qual a vazão (ou bitrate) você quer para o TCP {i+1} (em Mb, enter para Ilimitado): "
            )

            tcp_clients.append((tcp_port, tcp_bitrate, cong_alg))
            tcp_port += 1

    print("\nPara o UDP:\n")

    # udp_port = input(
    #     "Digite a porta para o UDP (Pressione Enter para a porta padrão 5202): "
    # )

    # if udp_port == "":
    udp_port = 5201

    udp_bitrate = ""

    while udp_bitrate == "":
        udp_bitrate = input(
            "Qual a vazão (ou bitrate) você quer para o UDP (em Mb): ")
        if udp_bitrate == "":
            print("UDP precisa de um valor de bitrate!", end=" ")

    # Cria Threads para cada cliente
    tcp_threads = []

    if num_tcp == 1:
        tcp_thread = threading.Thread(
            target=run_iperf_tcp_client,
            args=(server_ip, tcp_port, str(duration + atraso),
                  tcp_bitrate, cong_alg, json),
        )
    else:
        for tcp_client in tcp_clients:
            # 0 = port, 1 = bitrate, 2 = cong_alg
            tcp_threads.append(threading.Thread(target=run_iperf_tcp_client, args=(
                server_ip, tcp_client[0], str(duration + atraso), tcp_client[1], tcp_client[2], json)))

    udp_thread = threading.Thread(
        target=run_iperf_udp_client,
        args=(server_ip, udp_port, duration, udp_bitrate, json),
    )

    old_client_files = glob.glob('client*.json')
    for file in old_client_files:
        os.remove(file)

    # Inicia as threads
    print()

    if num_tcp == 1:
        tcp_thread.start()
        print(
            f"Iniciada conexão TCP para servidor {server_ip}:{tcp_port}{f' com {tcp_bitrate} Mb' if tcp_bitrate != '' else '' } e algoritmo de cong. {cong_alg.capitalize()}"
        )
    else:
        for i in range(len(tcp_clients)):
            tcp_threads[i].start()
            tcp_i_port, tcp_i_bitrate, cong_alg_i = tcp_clients[i]
            print(
                f"Iniciada conexão TCP para servidor {server_ip}:{tcp_i_port}{f' com {tcp_i_bitrate} Mb' if tcp_i_bitrate != '' else '' } e algoritmo de cong. {cong_alg_i.capitalize()}"
            )

    time.sleep(atraso)

    udp_thread.start()
    print(
        f"Iniciada conexão UDP para servidor {server_ip}:{udp_port} com bitrate de {udp_bitrate} Mb"
    )

    # Espera elas terminarem
    if num_tcp == 1:
        tcp_thread.join()
    else:
        for tcp_thread in tcp_threads:
            tcp_thread.join()

    udp_thread.join()
    print("\nFim das conexões!")


if __name__ == "__main__":
    main()
