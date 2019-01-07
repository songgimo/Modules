import csv


class CSVModule:
    def import_csv(self, csv_path):
        with open(csv_path, 'r', newline='') as rds:
            list_ = []
            for rd in csv.reader(rds):
                try:
                    list_.append(rd)
                except Exception as ex:
                    print(ex)
                    # logger.debug('csv import error [{}]'.format(ex))

            return list_

    def export_csv(self, csv_path, list_):
        with open(csv_path, 'a', newline='')as csvf:
            #
            writer = csv.writer(csvf)

            for li in list_:
                # li = [1, 2, 3] 형식이어야 함.
                try:
                    writer.writerow(li)
                except Exception as ex:
                    print(ex)
                    # logger.debug('csv export error [{}]'.format(ex))

            return True
