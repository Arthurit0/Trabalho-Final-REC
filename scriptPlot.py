import json
import glob
import matplotlib.pyplot as plt


def main():

    type = ''

    while type not in ['1', '2']:
        type = input(
            "Deseja gerar o gráfico para (1) Servidores ou (2) Clientes? ")
        if type not in ['1', '2']:
            print("Escolha um dos tipos digitando '1' ou '2'!")

    offset = input("Quantos segundos de atraso do UDP? ")

    if offset == '':
        offset = 0  # se nenhum offset for fornecido, definimos como 0
    else:
        offset = int(offset)

    if type == '1':
        type = 'server'
    else:
        type = 'client'

    json_files = glob.glob(f'{type}*.json')

    metrics_data = {}
    all_metrics = ['bytes', 'bits_per_second', 'retransmits',
                   'max_snd_cwnd', 'jitter_ms', 'lost_packets', 'packets']

    for file in json_files:
        print(f'Lendo e processando arquivo: {file}')

        with open(file) as json_file:
            data = json.load(json_file)

            if file not in metrics_data:
                metrics_data[file] = {}
                for metric in all_metrics:
                    metrics_data[file][metric] = []

            for i, interval in enumerate(data['intervals']):
                for stream in interval['streams']:
                    for metric in all_metrics:
                        if metric in stream:
                            metrics_data[file][metric].append(stream[metric])

    for filename, data in metrics_data.items():
        port = filename.replace(f'port_', '').replace('.json', '')

        with open(filename) as json_file:
            json_data = json.load(json_file)
            protocol = json_data['start']['test_start']['protocol'].upper()

            cong_alg = json_data.get('end', []).get(
                'receiver_tcp_congestion', '')

        for metric in all_metrics:
            if data[metric]:
                legend_label = f'{type} - porta {port} ({protocol}{", " + cong_alg if cong_alg else ""})'

                x_axis = range(len(data[metric]))
                y_axis = data[metric]

                if protocol == 'UDP':
                    x_axis = [x + offset for x in x_axis]

                plt.figure(metric)
                plt.plot(x_axis, y_axis, label=f'{legend_label}')
                plt.title(f"Comparação de {metric}")
                plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
