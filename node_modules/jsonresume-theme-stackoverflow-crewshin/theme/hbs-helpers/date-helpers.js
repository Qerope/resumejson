const moment = require('moment');

const dateHelpers = {
  MY: date => {
    if (typeof date === 'string') {
      return date;
    }
    return moment(date.toString(), ['YYYY-MM-DD']).format('MMM YYYY');
  },
  Y: date => {
    if (typeof date === 'string') {
      return date;
    }
    return moment(date.toString(), ['YYYY-MM-DD']).format('YYYY');
  },
  DMY: date => {
    if (typeof date === 'string') {
      return date;
    }
    return moment(date.toString(), ['YYYY-MM-DD']).format('D MMM YYYY');
  }
};

module.exports = { dateHelpers };
